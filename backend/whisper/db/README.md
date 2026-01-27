# Database Module

Domain-driven database architecture with reusable components.

## Quick Start

```python
from db.manager import DatabaseManager

db = DatabaseManager()
db.init_database()

# Use any domain
db.lectures.get_all_ids()
db.vtt_files.save(123, "en", True)
db.api_keys.add("key", "name", "email")
db.blacklist.add(999, "error")
```

## Architecture

- **base/** - Reusable connection and repository classes
- **domains/** - Domain-specific repositories (lectures, vtt_files, api_keys, blacklist)
- **manager.py** - Unified access to all domains

## Adding Domains

```python
from ..base.repository import BaseRepository

class MyRepository(BaseRepository):
    def init_tables(self):
        schema = "CREATE TABLE ..."
        self.create_tables(schema)
```

Register in `manager.py` and use: `db.my_domain.operation()`

## Features

- Context managers for safe connections
- Type hints throughout
- Automatic commit/rollback
- Easy to extend and test
