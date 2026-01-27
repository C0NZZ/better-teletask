"""
Unified database manager that combines all repositories and provides
initialization and utility functions.
"""
from typing import List
import logging
from .base.connection import DatabaseConnection
from .domains.lectures import LectureRepository
from .domains.vtt_files import VTTFileRepository
from .domains.api_keys import APIKeyRepository
from .domains.blacklist import BlacklistRepository

logger = logging.getLogger("btt_root_logger")


class DatabaseManager:
    """
    Main database manager that provides access to all domain repositories
    and handles initialization.
    """
    
    def __init__(self):
        self.connection = DatabaseConnection()
        self.lectures = LectureRepository(self.connection)
        self.vtt_files = VTTFileRepository(self.connection)
        self.api_keys = APIKeyRepository(self.connection)
        self.blacklist = BlacklistRepository(self.connection)
    
    def init_database(self):
        """Initialize all tables in the database."""
        logger.info("Initializing database tables...")
        self.lectures.init_tables()
        self.vtt_files.init_tables()
        self.api_keys.init_tables()
        self.blacklist.init_tables()
        logger.info("Database initialization complete.")
    
    def clear_database(self):
        """Drop all tables in the database."""
        logger.warning("Clearing database...")
        all_tables = (
            self.vtt_files.tables +
            self.lectures.tables +
            self.api_keys.tables +
            self.blacklist.tables
        )
        self.lectures.drop_tables(all_tables)
        logger.warning("Database cleared.")
    
    def get_missing_available_inbetween_ids(self) -> List[int]:
        """Get missing IDs that are not blacklisted."""
        initial_ids = self.vtt_files.get_missing_inbetween_ids()
        blacklisted_ids = self.blacklist.get_all()
        available_ids = list(set(initial_ids) - set(blacklisted_ids))
        logger.debug(f"Missing available IDs: {available_ids}")
        return available_ids
