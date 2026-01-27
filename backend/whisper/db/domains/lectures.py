from datetime import datetime
from typing import Optional, Dict, Any
import logging
from ..base.repository import BaseRepository

logger = logging.getLogger("btt_root_logger")


LECTURE_SCHEMA = """
CREATE TABLE IF NOT EXISTS series_data (
    series_id INTEGER PRIMARY KEY,
    series_name VARCHAR(255),
    lecturer_id VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lecturer_data (
    lecturer_id INTEGER PRIMARY KEY,
    lecturer_name VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lecture_data (
    teletask_id INTEGER PRIMARY KEY, 
    language VARCHAR(50),
    date DATE,
    lecturer_id INTEGER,
    series_id INTEGER,
    semester VARCHAR(50),
    duration INTERVAL,
    title VARCHAR(255),
    video_mp4 VARCHAR(255),
    desktop_mp4 VARCHAR(255),
    podcast_mp4 VARCHAR(255)
);
"""


class LectureRepository(BaseRepository):
    """Repository for lecture-related operations."""
    
    def __init__(self, db_connection):
        super().__init__(db_connection)
        self.tables = ['lecture_data', 'series_data', 'lecturer_data']
    
    def init_tables(self):
        """Initialize lecture tables."""
        self.create_tables(LECTURE_SCHEMA)
    
    def series_exists(self, series_id: int) -> bool:
        """Check if series exists."""
        return self.exists('series_data', 'series_id', series_id)
    
    def lecturer_exists(self, lecturer_id: int) -> bool:
        """Check if lecturer exists."""
        return self.exists('lecturer_data', 'lecturer_id', lecturer_id)
    
    def get_all_ids(self):
        """Get all lecture IDs."""
        return super().get_all_ids('lecture_data', 'teletask_id')
    
    def get_language(self, teletask_id: int) -> Optional[str]:
        """Get language of a lecture."""
        query = "SELECT language FROM lecture_data WHERE teletask_id = %s;"
        row = self.execute_query(query, (teletask_id,), fetch_one=True)
        if row:
            return row[0]
        else:
            logger.info(f"No lecture data found for Teletask ID: {teletask_id}")
            return None
    
    def add(self, lecture_data: Dict[str, Any]):
        """Add lecture data along with series and lecturer information."""
        teletaskid = lecture_data['teletask_id']
        lecturer_id = lecture_data['lecturer_id']
        lecturer_name = lecture_data['lecturer_name']
        date = lecture_data['date']
        date = datetime.strptime(date, "%B %d, %Y")
        language = lecture_data['language']
        language = "en" if language == "English" else "de"
        duration = lecture_data['duration']
        lecture_title = lecture_data['lecture_title']
        series_id = lecture_data['series_id']
        series_name = lecture_data['series_name']
        url = lecture_data['url']
        
        if date.month < 3 or date.month > 10:
            semester = f"WT {date.year-1}/{date.year}"
        else:
            semester = f"ST {date.year}"
        
        try:
            with self.db.get_cursor() as (cur, conn):
                if not self.lecturer_exists(lecturer_id):
                    cur.execute(
                        "INSERT INTO lecturer_data (lecturer_id, lecturer_name) VALUES (%s, %s) ON CONFLICT (lecturer_id) DO NOTHING;",
                        (lecturer_id, lecturer_name),
                    )
                    logger.info(f"Added lecturer data for Lecturer ID {lecturer_id}.", extra={'id': teletaskid})
                
                if not self.series_exists(series_id):
                    cur.execute(
                        "INSERT INTO series_data (series_id, series_name, lecturer_id) VALUES (%s, %s, %s) ON CONFLICT (series_id) DO NOTHING;",
                        (series_id, series_name, lecturer_id),
                    )
                    logger.info(f"Added series data for Series ID {series_id}.", extra={'id': teletaskid})
                
                cur.execute(
                    "INSERT INTO lecture_data (teletask_id, language, date, lecturer_id, series_id, semester, duration, title, video_mp4) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
                    (teletaskid, language, date, lecturer_id, series_id, semester, duration, lecture_title, url),
                )
        except Exception as error:
            logger.error(f"Error adding lecture data: {error}")
            raise
