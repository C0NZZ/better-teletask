# Modular Database System

Your monolithic `database.py` has been refactored into a modular, domain-driven architecture.

## Structure

```
db/
├── base/
│   ├── connection.py      # Connection management
│   └── repository.py      # Base repository class
├── domains/
│   ├── lectures.py        # Lectures, series, lecturers
│   ├── vtt_files.py       # VTT file storage
│   ├── api_keys.py        # API key management
│   └── blacklist.py       # Blacklist tracking
└── manager.py             # Unified access
```

## Usage

### Option 1: Backward Compatible (Zero Changes)
```python
import database_new as database

database.initDatabase()
ids = database.get_all_lecture_ids()
# All old functions work exactly the same
```

### Option 2: Use Manager (Recommended)
```python
from db.manager import DatabaseManager

db = DatabaseManager()
db.init_database()

# Clean, organized access
db.lectures.get_all_ids()
db.vtt_files.save(123, "en", True)
db.api_keys.add("key", "name", "email")
db.blacklist.add(999, "error")
```

## API Reference

### Lectures
```python
db.lectures.get_all_ids()           # All lecture IDs
db.lectures.series_exists(id)       # Check series
db.lectures.lecturer_exists(id)     # Check lecturer
db.lectures.add(lecture_data)       # Add lecture
db.lectures.get_language(id)        # Get language
```

### VTT Files
```python
db.vtt_files.get_all_original_ids() # Original files
db.vtt_files.original_exists(id)    # Check if exists
db.vtt_files.save(id, lang, orig)   # Save file
db.vtt_files.get_all_blobs()        # All files
db.vtt_files.get_highest_id()       # Max ID
db.vtt_files.get_smallest_id()      # Min ID
db.vtt_files.get_missing_inbetween_ids()  # Missing IDs
```

### API Keys
```python
db.api_keys.add(key, name, email)   # Add key
db.api_keys.get_by_key(key)         # Get by key
db.api_keys.get_by_name(name)       # Get by name
db.api_keys.get_all()               # All keys
db.api_keys.remove(key)             # Remove key
```

### Blacklist
```python
db.blacklist.add(id, reason)        # Add to blacklist
db.blacklist.get_all()              # All blacklisted
db.blacklist.contains(id)           # Check if blacklisted
```

## Adding New Domains

```python
# 1. Create db/domains/my_domain.py
from ..base.repository import BaseRepository

SCHEMA = "CREATE TABLE IF NOT EXISTS ..."

class MyDomainRepository(BaseRepository):
    def init_tables(self):
        self.create_tables(SCHEMA)
    
    def my_operation(self):
        # Your code here
        pass

# 2. Register in db/manager.py
class DatabaseManager:
    def __init__(self):
        # ...
        self.my_domain = MyDomainRepository(self.connection)
    
    def init_database(self):
        # ...
        self.my_domain.init_tables()

# 3. Use it!
db.my_domain.my_operation()
```

## Benefits

- **Modular**: Each domain is self-contained
- **Clean API**: `db.api_keys.add()` not `db.add_api_key()`
- **Extensible**: Add domains without touching core
- **Reusable**: Copy domains to other projects
- **Type hints**: Full IDE support
- **Safe**: Context managers prevent connection leaks
- **Backward compatible**: Old code still works

## Migration

See `MIGRATION.md` for detailed migration guide.
