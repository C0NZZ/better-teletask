import psycopg2
from psycopg2 import extensions
from contextlib import contextmanager
import logging
from config import get_config

logger = logging.getLogger("btt_root_logger")


class DatabaseConnection:
    """Manages database connection parameters and provides connection context managers."""
    
    def __init__(self):
        config = get_config()
        self.db_name = config.postgres_db
        self.db_user = config.postgres_user
        self.db_pass = config.postgres_password
        self.db_host = config.db_host
        self.db_port = config.db_port
    
    @contextmanager
    def get_connection(self, autocommit=False):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_pass,
                host=self.db_host,
                port=self.db_port
            )
            if autocommit:
                conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            yield conn
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Database connection error: {error}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, autocommit=False):
        """Context manager for database cursor."""
        with self.get_connection(autocommit=autocommit) as conn:
            cur = conn.cursor()
            try:
                yield cur, conn
                if not autocommit:
                    conn.commit()
            except Exception as e:
                if not autocommit:
                    conn.rollback()
                raise
            finally:
                cur.close()
