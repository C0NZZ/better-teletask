from typing import List, Dict, Optional
import logging
from ..base.repository import BaseRepository

logger = logging.getLogger("btt_root_logger")


API_KEYS_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    person_name VARCHAR(255),
    person_email VARCHAR(255),
    creation_date TIMESTAMPTZ DEFAULT NOW(),
    expiration_date TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '3 months'),
    status VARCHAR(255) DEFAULT 'active'
);
CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys (api_key);
"""


class APIKeyRepository(BaseRepository):
    """Repository for API key operations."""
    
    def __init__(self, db_connection):
        super().__init__(db_connection)
        self.tables = ['api_keys']
    
    def init_tables(self):
        """Initialize API keys table."""
        self.create_tables(API_KEYS_SCHEMA)
    
    def add(self, api_key: str, person_name: str, person_email: str):
        """Add a new key."""
        query = """
            INSERT INTO api_keys (api_key, person_name, person_email) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (api_key) DO NOTHING;
        """
        self.execute_query(query, (api_key, person_name, person_email))
    
    def get_by_key(self, api_key: str) -> Optional[Dict]:
        """Get details by key."""
        query = """
            SELECT api_key, person_name, person_email, creation_date, expiration_date, status 
            FROM api_keys WHERE api_key = %s;
        """
        row = self.execute_query(query, (api_key,), fetch_one=True)
        
        if row:
            return {
                "api_key": row[0],
                "person_name": row[1],
                "person_email": row[2],
                "creation_date": row[3],
                "expiration_date": row[4],
                "status": row[5]
            }
        else:
            logger.info(f"No API key found: {api_key}")
            return None
    
    def get_by_name(self, person_name: str) -> Optional[List[Dict]]:
        """Get all keys for a person by name."""
        query = """
            SELECT api_key, person_name, person_email, creation_date, expiration_date, status 
            FROM api_keys WHERE person_name = %s;
        """
        rows = self.execute_query(query, (person_name,), fetch_all=True)
        
        if rows:
            keys = []
            for row in rows:
                keys.append({
                    "api_key": row[0],
                    "person_name": row[1],
                    "person_email": row[2],
                    "creation_date": row[3],
                    "expiration_date": row[4],
                    "status": row[5]
                })
            return keys
        else:
            logger.info(f"No API key found for person name: {person_name}")
            return None
    
    def get_all(self) -> List[Dict]:
        """Get all keys."""
        query = "SELECT api_key, person_name, person_email, creation_date, expiration_date, status FROM api_keys;"
        rows = self.execute_query(query, fetch_all=True)
        
        keys = []
        if rows:
            for row in rows:
                keys.append({
                    "api_key": row[0],
                    "person_name": row[1],
                    "person_email": row[2],
                    "creation_date": row[3],
                    "expiration_date": row[4],
                    "status": row[5]
                })
        
        return keys
    
    def remove(self, api_key: str):
        """Remove a key."""
        query = "DELETE FROM api_keys WHERE api_key = %s;"
        self.execute_query(query, (api_key,))
        logger.info(f"Successfully removed API key: {api_key}")
