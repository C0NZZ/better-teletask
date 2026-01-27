"""
Usage examples for the modular database system.
"""
import logging
from db.manager import DatabaseManager
from db.base.connection import DatabaseConnection
from db.domains.lectures import LectureRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("btt_root_logger")


def example_1_basic_usage():
    """Example 1: Basic usage with manager"""
    print("\n=== Example 1: Basic Usage ===")
    
    db = DatabaseManager()
    db.init_database()
    
    # Work with domains
    lecture_ids = db.lectures.get_all_ids()
    print(f"Lectures: {len(lecture_ids)}")
    
    highest_id = db.vtt_files.get_highest_id()
    print(f"Highest ID: {highest_id}")
    
    all_keys = db.api_keys.get_all()
    print(f"API keys: {len(all_keys)}")


def example_2_backward_compatible():
    """Example 2: Using backward compatible wrapper"""
    print("\n=== Example 2: Backward Compatible ===")
    
    import database_new as database
    
    database.initDatabase()
    ids = database.get_all_lecture_ids()
    print(f"Lectures: {len(ids)}")


def example_3_individual_repository():
    """Example 3: Using individual repository"""
    print("\n=== Example 3: Individual Repository ===")
    
    conn = DatabaseConnection()
    lectures = LectureRepository(conn)
    lectures.init_tables()
    
    lecture_ids = lectures.get_all_ids()
    print(f"Lectures: {len(lecture_ids)}")


def example_4_transactions():
    """Example 4: Transaction handling"""
    print("\n=== Example 4: Transactions ===")
    
    db = DatabaseManager()
    
    try:
        with db.connection.get_cursor() as (cur, conn):
            cur.execute("INSERT INTO lecturer_data (lecturer_id, lecturer_name) VALUES (%s, %s);", 
                       (999, "Test"))
            cur.execute("INSERT INTO series_data (series_id, series_name, lecturer_id) VALUES (%s, %s, %s);",
                       (999, "Test Series", 999))
        print("Transaction committed")
    except Exception as e:
        print(f"Transaction failed: {e}")


def example_5_custom_domain():
    """Example 5: Creating a custom domain"""
    print("\n=== Example 5: Custom Domain ===")
    
    from db.base.repository import BaseRepository
    
    class CustomRepository(BaseRepository):
        def init_tables(self):
            schema = """
            CREATE TABLE IF NOT EXISTS custom_data (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255)
            );
            """
            self.create_tables(schema)
        
        def add_item(self, name):
            query = "INSERT INTO custom_data (name) VALUES (%s);"
            self.execute_query(query, (name,))
    
    conn = DatabaseConnection()
    custom = CustomRepository(conn)
    custom.init_tables()
    print("Custom domain ready")


if __name__ == "__main__":
    print("Database Examples")
    print("=" * 50)
    
    try:
        example_1_basic_usage()
        example_2_backward_compatible()
        example_3_individual_repository()
        example_4_transactions()
        example_5_custom_domain()
        
        print("\n" + "=" * 50)
        print("All examples completed!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure database is configured in .env")
