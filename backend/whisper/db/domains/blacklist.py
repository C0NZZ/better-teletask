from typing import List
import logging
from ..base.repository import BaseRepository

logger = logging.getLogger("btt_root_logger")


BLACKLIST_SCHEMA = """
CREATE TABLE IF NOT EXISTS blacklist_ids (
    teletask_id INTEGER PRIMARY KEY,
    reason VARCHAR(255),
    times_tried INTEGER DEFAULT 1,
    creation_date TIMESTAMPTZ DEFAULT NOW()
);
"""


class BlacklistRepository(BaseRepository):
    """Repository for blacklist operations."""
    
    def __init__(self, db_connection):
        super().__init__(db_connection)
        self.tables = ['blacklist_ids']
    
    def init_tables(self):
        """Initialize blacklist table."""
        self.create_tables(BLACKLIST_SCHEMA)
    
    def add(self, teletask_id: int, reason: str):
        """Add ID or increment retry count."""
        query = """
            INSERT INTO blacklist_ids (teletask_id, reason) 
            VALUES (%s, %s) 
            ON CONFLICT (teletask_id) DO UPDATE 
            SET times_tried = blacklist_ids.times_tried + 1, 
                reason = EXCLUDED.reason;
        """
        self.execute_query(query, (teletask_id, reason))
        logger.info(f"Successfully added Teletask ID {teletask_id} to blacklist.")
    
    def get_all(self) -> List[int]:
        """Get all IDs."""
        return self.get_all_ids('blacklist_ids', 'teletask_id')
    
    def contains(self, teletask_id: int) -> bool:
        """Check if ID is blacklisted."""
        return self.exists('blacklist_ids', 'teletask_id', teletask_id)
