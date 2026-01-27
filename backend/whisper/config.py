"""
Configuration manager singleton.
Centralized access to environment variables with hot-reloading support.
"""
import os
from typing import Optional
from dotenv import load_dotenv, find_dotenv
import logging

logger = logging.getLogger("btt_root_logger")


class Config:
    """Singleton configuration manager."""
    
    _instance: Optional['Config'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Config._initialized:
            self._load_env()
            self._load_config()
            Config._initialized = True
    
    def _load_env(self):
        """Load environment variables from .env file."""
        load_dotenv(find_dotenv())
    
    def _load_config(self):
        """Load all configuration values."""
        # Database
        self.postgres_db = os.environ.get("POSTGRES_DB")
        self.postgres_user = os.environ.get("POSTGRES_USER")
        self.postgres_password = os.environ.get("POSTGRES_PASSWORD")
        self.db_host = os.environ.get("DB_HOST")
        self.db_port = os.environ.get("DB_PORT")
        
        # Whisper
        self.asr_model = os.environ.get("ASR_MODEL")
        self.compute_type = os.environ.get("COMPUTE_TYPE")
        
        # Folders
        self.vtt_dest_folder = os.environ.get("VTT_DEST_FOLDER")
        self.recording_source_folder = os.environ.get("RECORDING_SOURCE_FOLDER")
        
        # Session (hot-reloadable)
        self._username_cookie = os.environ.get("USERNAME_COOKIE")
    
    @property
    def username_cookie(self) -> str:
        """Get username cookie with hot-reload support."""
        # Reload from environment each time
        self._load_env()
        new_value = os.environ.get("USERNAME_COOKIE")
        if new_value != self._username_cookie:
            logger.info("Session cookie reloaded from environment")
            self._username_cookie = new_value
        return self._username_cookie
    
    def reload(self):
        """Manually reload all configuration from .env file."""
        logger.info("Reloading configuration from .env")
        self._load_env()
        self._load_config()
    
    def get(self, key: str, default=None):
        """Get a config value by key."""
        return getattr(self, key, default)


# Singleton instance
_config = Config()


def get_config() -> Config:
    """Get the singleton config instance."""
    return _config
