"""
Backward-compatible wrapper for the modular database.
Provides the same function interface as the original database.py
"""
from db.manager import DatabaseManager

# Initialize global database manager
_db_manager = DatabaseManager()


# Initialization functions
def initDatabase():
    """Initialize database tables."""
    _db_manager.init_database()


def clearDatabase():
    """Clear all database tables."""
    _db_manager.clear_database()


# Lecture functions
def get_all_lecture_ids():
    """Get all lecture IDs."""
    return _db_manager.lectures.get_all_ids()


def series_id_exists(series_id):
    """Check if series exists."""
    return _db_manager.lectures.series_exists(series_id)


def lecturer_id_exists(lecturer_id):
    """Check if lecturer exists."""
    return _db_manager.lectures.lecturer_exists(lecturer_id)


def add_lecture_data(lecture_data):
    """Add lecture data."""
    _db_manager.lectures.add(lecture_data)


def get_language_of_lecture(teletaskid):
    """Get language of a lecture."""
    return _db_manager.lectures.get_language(teletaskid)


# VTT file functions
def get_all_original_vtt_ids():
    """Get all original VTT IDs."""
    return _db_manager.vtt_files.get_all_original_ids()


def original_language_exists(teletaskid):
    """Check if original language VTT exists."""
    return _db_manager.vtt_files.original_exists(teletaskid)


def save_vtt_as_blob(teletaskid, language, isOriginalLang):
    """Save VTT as blob."""
    return _db_manager.vtt_files.save(teletaskid, language, isOriginalLang)


def get_all_vtt_blobs():
    """Get all VTT blobs."""
    return _db_manager.vtt_files.get_all_blobs()


def getHighestTeletaskID():
    """Get highest teletask ID."""
    return _db_manager.vtt_files.get_highest_id()


def getSmallestTeletaskID():
    """Get smallest teletask ID."""
    return _db_manager.vtt_files.get_smallest_id()


def get_missing_inbetween_ids():
    """Get missing IDs between min and max."""
    return _db_manager.vtt_files.get_missing_inbetween_ids()


def get_missing_translations():
    """Get missing translations."""
    return _db_manager.vtt_files.get_missing_translations()


# API key functions
def add_api_key(api_key, person_name, person_email):
    """Add API key."""
    _db_manager.api_keys.add(api_key, person_name, person_email)


def get_api_key_by_key(api_key):
    """Get API key by key."""
    return _db_manager.api_keys.get_by_key(api_key)


def get_api_key_by_name(person_name):
    """Get API key by name."""
    return _db_manager.api_keys.get_by_name(person_name)


def get_all_api_keys():
    """Get all API keys."""
    return _db_manager.api_keys.get_all()


def remove_api_key(api_key):
    """Remove API key."""
    _db_manager.api_keys.remove(api_key)


# Blacklist functions
def add_id_to_blacklist(teletaskid, reason):
    """Add ID to blacklist."""
    _db_manager.blacklist.add(teletaskid, reason)


def get_blacklisted_ids():
    """Get blacklisted IDs."""
    return _db_manager.blacklist.get_all()


def get_missing_available_inbetween_ids():
    """Get missing available IDs (not blacklisted)."""
    return _db_manager.get_missing_available_inbetween_ids()


# Expose the manager for direct access if needed
db_manager = _db_manager


if __name__ == "__main__":
    initDatabase()
