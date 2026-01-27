# Migration Guide

## Quick Start (Zero Changes)

Simply replace your import:

```python
# Before
import database

# After
import database_new as database
```

That's it! All functions work exactly the same.

## Function Mapping

### Old → New (Manager)

```python
# Initialization
database.initDatabase()                 → db.init_database()
database.clearDatabase()                → db.clear_database()

# Lectures
database.get_all_lecture_ids()          → db.lectures.get_all_ids()
database.series_id_exists(id)           → db.lectures.series_exists(id)
database.lecturer_id_exists(id)         → db.lectures.lecturer_exists(id)
database.add_lecture_data(data)         → db.lectures.add(data)
database.get_language_of_lecture(id)    → db.lectures.get_language(id)

# VTT Files
database.get_all_original_vtt_ids()     → db.vtt_files.get_all_original_ids()
database.original_language_exists(id)   → db.vtt_files.original_exists(id)
database.save_vtt_as_blob(...)          → db.vtt_files.save(...)
database.get_all_vtt_blobs()            → db.vtt_files.get_all_blobs()
database.getHighestTeletaskID()         → db.vtt_files.get_highest_id()
database.getSmallestTeletaskID()        → db.vtt_files.get_smallest_id()
database.get_missing_inbetween_ids()    → db.vtt_files.get_missing_inbetween_ids()

# API Keys
database.add_api_key(...)               → db.api_keys.add(...)
database.get_api_key_by_key(key)        → db.api_keys.get_by_key(key)
database.get_api_key_by_name(name)      → db.api_keys.get_by_name(name)
database.get_all_api_keys()             → db.api_keys.get_all()
database.remove_api_key(key)            → db.api_keys.remove(key)

# Blacklist
database.add_id_to_blacklist(...)       → db.blacklist.add(...)
database.get_blacklisted_ids()          → db.blacklist.get_all()
```

## Migration Phases

### Phase 1: Wrapper (Day 1)
Use backward compatible wrapper - zero code changes needed.

```python
import database_new as database
# Everything works the same
```

### Phase 2: Gradual (Week 2+)
New code uses manager, old code uses wrapper.

```python
# New code
from db.manager import DatabaseManager
db = DatabaseManager()
db.lectures.get_all_ids()

# Old code still works
import database_new as database
database.get_all_lecture_ids()
```

### Phase 3: Complete (Ongoing)
Update old code as you touch it.

```python
# Refactor from
database.get_all_lecture_ids()

# To
db.lectures.get_all_ids()
```

## Example Refactor

### Before
```python
import database

database.initDatabase()
lecture_ids = database.get_all_lecture_ids()
database.save_vtt_as_blob(123, "en", True)
database.add_api_key("key", "John", "john@mail.com")

if not database.get_blacklisted_ids():
    # process
    pass
```

### After (Wrapper)
```python
import database_new as database

database.initDatabase()
lecture_ids = database.get_all_lecture_ids()
database.save_vtt_as_blob(123, "en", True)
database.add_api_key("key", "John", "john@mail.com")

if not database.get_blacklisted_ids():
    # process
    pass
```

### After (Manager)
```python
from db.manager import DatabaseManager

db = DatabaseManager()
db.init_database()
lecture_ids = db.lectures.get_all_ids()
db.vtt_files.save(123, "en", True)
db.api_keys.add("key", "John", "john@mail.com")

if not db.blacklist.get_all():
    # process
    pass
```

## Tips

1. **Start with wrapper** - No code changes needed
2. **Test thoroughly** - Verify everything works
3. **Refactor gradually** - Update as you touch files
4. **Keep old database.py** - As backup during migration
5. **Use type hints** - New system has full type support

## Rollback

If needed, simply change imports back:
```python
import database  # Back to original
```

The old `database.py` file remains unchanged.
