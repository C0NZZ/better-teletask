import psycopg2
import os
from dotenv import load_dotenv, find_dotenv

# Load the .env file
load_dotenv(find_dotenv())
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "output/")

# --- Database Connection Details ---
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASS = os.environ.get("POSTGRES_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

def initDatabse():
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        
        print("connected")

        # --- Create Table (if it doesn't exist) ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vtt_files (
                id SERIAL PRIMARY KEY,
                teletaskid VARCHAR(255) NOT NULL,
                language VARCHAR(255) NOT NULL,
                isOriginalLanguage BOOLEAN NOT NULL,
                vtt_data BYTEA NOT NULL
            );
        """)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def clearDatabase():
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        conn.autocommit = False
        cur = conn.cursor()
        
        print("connected")

        cur.execute("""
            DROP TABLE "vtt_files";
        """)
        conn.commit()

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def save_vtt_as_blob(teletaskid, language, isOriginalLanguage):
    conn = None
    file_path = os.path.join(input_path, teletaskid+".vtt")
    print(file_path)
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Create Table (if it doesn't exist) ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vtt_files (
                id SERIAL PRIMARY KEY,
                teletaskid VARCHAR(255) NOT NULL,
                language VARCHAR(255) NOT NULL,
                isOriginalLanguage BOOLEAN NOT NULL,
                vtt_data BYTEA NOT NULL
            );
        """)

        print(f"Teletask ID: {teletaskid}")
        print(f"Language: {language}")
        print(f"Is Original Language: {isOriginalLanguage}")

        # --- Read file in binary mode and insert ---
        with open(file_path, 'rb') as f:
            vtt_binary_data = f.read()
        
        cur.execute(
            "INSERT INTO vtt_files (teletaskid,language,isOriginalLanguage,vtt_data) VALUES (%s,%s,%s,%s);",
            (teletaskid,language,isOriginalLanguage,vtt_binary_data)
        )
        
        conn.commit()
        print(f"Successfully saved '{file_path}' as a BLOB.")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def get_all_vtt_blobs():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute("SELECT id, teletaskid, language,isOriginalLanguage, vtt_data FROM vtt_files ORDER BY id;")
        rows = cur.fetchall()
        
        print(f"\n=== Found {len(rows)} VTT file(s) in database ===\n")
        
        for row in rows:
            record_id, teletaskid, language,isOriginalLanguage, vtt_data = row
            print(f"--- Record ID: {record_id} ---")
            print(f"Teletask ID: {teletaskid}")
            print(f"Language: {language}")
            print(f"Is Original Language: {isOriginalLanguage}")
            print(f"VTT Data (size): {len(vtt_data)} bytes")
            print(f"VTT Content:")
            print("-" * 50)
                # Convert memoryview to bytes, then decode to string for display
            try:
                vtt_bytes = bytes(vtt_data)
                vtt_content = vtt_bytes.decode('utf-8')
                print(vtt_content)
            except UnicodeDecodeError:
                print("(Binary data could not be decoded as UTF-8)")
            print("-" * 50)
            print()
        
        return rows

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
        return []
    finally:
        if conn:
            cur.close()
            conn.close()


def databaseTestScript():
    # --- Example Usage ---
    # Create a dummy file first
    with open("sample.vtt", "w") as f:
        f.write("WEBVTT\n\n00:00:01.000 --> 00:00:14.000\nHello world.")
    initDatabse()
    save_vtt_as_blob("1","de")

    # Query and print all blobs
    get_all_vtt_blobs()

if __name__ == '__main__':
    get_all_vtt_blobs()
    #databaseTestScript()
