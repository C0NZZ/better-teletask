import os
from typing import List, Tuple, Optional
import logging
from ..base.repository import BaseRepository
from config import get_config

logger = logging.getLogger("btt_root_logger")


VTT_FILES_SCHEMA = """
CREATE TABLE IF NOT EXISTS vtt_files (
    id SERIAL PRIMARY KEY,
    teletask_id INTEGER NOT NULL,
    language VARCHAR(50) NOT NULL,
    is_original_lang BOOLEAN NOT NULL,
    vtt_data BYTEA NOT NULL,
    txt_data BYTEA NOT NULL,
    asr_model VARCHAR(255),
    compute_type VARCHAR(255),
    creation_date TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_vtt_files_teletask_id ON vtt_files (teletask_id);
"""


class VTTFileRepository(BaseRepository):
    """Repository for VTT file operations."""
    
    def __init__(self, db_connection):
        super().__init__(db_connection)
        self.tables = ['vtt_files']
        
        config = get_config()
        self.output_folder = config.vtt_dest_folder
        self.model = config.asr_model
        self.compute_type = config.compute_type
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_path = os.path.join(script_dir, '..', '..', self.output_folder)
    
    def init_tables(self):
        """Initialize VTT files table."""
        self.create_tables(VTT_FILES_SCHEMA)
    
    def get_all_original_ids(self) -> List[int]:
        """Get all IDs with original language files."""
        query = "SELECT teletask_id FROM vtt_files WHERE is_original_lang = TRUE;"
        rows = self.execute_query(query, fetch_all=True)
        ids = [row[0] for row in rows] if rows else []
        logger.debug(f"Fetched all original VTT IDs: {ids}")
        return ids
    
    def original_exists(self, teletask_id: int) -> bool:
        """Check if original language file exists."""
        query = "SELECT COUNT(*) FROM vtt_files WHERE teletask_id = %s AND is_original_lang = TRUE;"
        result = self.execute_query(query, (teletask_id,), fetch_one=True)
        return result[0] > 0 if result else False
    
    def save(self, teletask_id: int, language: str, is_original_lang: bool) -> int:
        """Save VTT and TXT files as blobs."""
        file_path = os.path.join(self.input_path, str(teletask_id) + ".vtt")
        file_path_txt = os.path.join(self.input_path, str(teletask_id) + ".txt")
        
        if not os.path.exists(file_path):
            logger.error(f"VTT file not found, cant put in database: {file_path}", extra={'id': teletask_id})
            return -1
        if not os.path.exists(file_path_txt):
            logger.error(f"TXT file not found, cant put in database: {file_path_txt}", extra={'id': teletask_id})
            return -1
        
        try:
            with open(file_path, "rb") as f:
                vtt_binary_data = f.read()
            
            with open(file_path_txt, "rb") as f:
                txt_binary_data = f.read()
            
            query = """
                INSERT INTO vtt_files (teletask_id, language, is_original_lang, vtt_data, txt_data, asr_model, compute_type) 
                VALUES (%s,%s,%s,%s,%s,%s,%s);
            """
            self.execute_query(query, (teletask_id, language, is_original_lang, vtt_binary_data, txt_binary_data, self.model, self.compute_type))
            logger.info(f"Successfully saved '{file_path}' as BLOB", extra={'id': teletask_id})
            return 0
        except Exception as error:
            logger.error(f"Error saving VTT as blob: {error}")
            return -1
    
    def get_all_blobs(self):
        """Retrieve all file records."""
        query = "SELECT id, teletask_id, language, is_original_lang, vtt_data, txt_data, compute_type FROM vtt_files ORDER BY id;"
        rows = self.execute_query(query, fetch_all=True)
        logger.info(f"Retrieved {len(rows) if rows else 0} VTT file(s) from database.")
        return rows if rows else []
    
    def get_highest_id(self) -> Optional[int]:
        """Get the highest teletask ID."""
        query = "SELECT MAX(teletask_id) FROM vtt_files;"
        result = self.execute_query(query, fetch_one=True)
        max_id = result[0] if result else None
        logger.info(f"Highest Teletask ID available in database: {max_id}")
        return max_id
    
    def get_smallest_id(self) -> Optional[int]:
        """Get the smallest teletask ID."""
        query = "SELECT MIN(teletask_id) FROM vtt_files;"
        result = self.execute_query(query, fetch_one=True)
        min_id = result[0] if result else None
        logger.info(f"Smallest Teletask ID available in database: {min_id}")
        return min_id
    
    def get_missing_inbetween_ids(self) -> List[int]:
        """Get missing teletask IDs between min and max."""
        query = """
            WITH bounds AS (
                SELECT 
                    MIN(teletask_id) AS min_id,
                    MAX(teletask_id) AS max_id
                FROM vtt_files
            ),
            all_ids AS (
                SELECT generate_series(
                    (SELECT min_id FROM bounds),
                    (SELECT max_id FROM bounds)
                ) AS teletask_id
            )
            SELECT all_ids.teletask_id
            FROM all_ids
            LEFT JOIN vtt_files vf 
                ON all_ids.teletask_id = vf.teletask_id
            WHERE vf.teletask_id IS NULL
            ORDER BY all_ids.teletask_id;
        """
        rows = self.execute_query(query, fetch_all=True)
        return [row[0] for row in rows] if rows else []
    
    def get_missing_translations(self) -> List[Tuple[int, str]]:
        """Get all translated (non-original) VTT files."""
        query = """
            WITH all_ids AS( SELECT DISTINCT teletask_id FROM vtt_files )
            SELECT teletask_id, language FROM vtt_files
            WHERE is_original_lang = False
            ORDER BY teletask_id DESC;
        """
        rows = self.execute_query(query, fetch_all=True)
        return [(row[0], row[1]) for row in rows] if rows else []
