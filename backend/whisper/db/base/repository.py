import logging
from typing import List, Optional

logger = logging.getLogger("btt_root_logger")


class BaseRepository:
    """Base repository with common database operations."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def execute_query(self, query: str, params: tuple = None, fetch_one=False, fetch_all=False):
        """Execute a query with automatic connection handling."""
        try:
            with self.db.get_cursor() as (cur, conn):
                cur.execute(query, params)
                if fetch_one:
                    return cur.fetchone()
                elif fetch_all:
                    return cur.fetchall()
                return None
        except Exception as error:
            logger.error(f"Query execution error: {error}")
            raise
    
    def exists(self, table: str, condition_field: str, condition_value) -> bool:
        """Check if a record exists in a table."""
        query = f"SELECT COUNT(*) FROM {table} WHERE {condition_field} = %s;"
        result = self.execute_query(query, (condition_value,), fetch_one=True)
        return result[0] > 0 if result else False
    
    def get_all_ids(self, table: str, id_field: str) -> List[int]:
        """Get all IDs from a table."""
        query = f"SELECT {id_field} FROM {table};"
        rows = self.execute_query(query, fetch_all=True)
        return [row[0] for row in rows] if rows else []
    
    def create_tables(self, schema_sql: str):
        """Create tables from schema SQL."""
        try:
            with self.db.get_cursor(autocommit=True) as (cur, conn):
                cur.execute(schema_sql)
                logger.info("Tables created successfully.")
        except Exception as error:
            logger.error(f"Error creating tables: {error}")
            raise
    
    def drop_tables(self, tables: List[str]):
        """Drop specified tables."""
        try:
            with self.db.get_cursor(autocommit=True) as (cur, conn):
                for table in tables:
                    cur.execute(f"DROP TABLE IF EXISTS {table};")
                logger.info(f"Dropped tables: {', '.join(tables)}")
        except Exception as error:
            logger.error(f"Error dropping tables: {error}")
            raise
