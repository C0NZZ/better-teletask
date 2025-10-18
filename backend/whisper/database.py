import psycopg2
import os
from dotenv import load_dotenv, find_dotenv

# Load the .env file
load_dotenv(find_dotenv())

# Read environment variables
API_TOKEN = os.environ.get("POSTGRES_PASSWORD")
print(API_TOKEN)

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

        # --- Create Table (if it doesn't exist) ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vtt_files (
                id SERIAL PRIMARY KEY,
                teletaskid VARCHAR(255) NOT NULL,
                language VARCHAR(255) NOT NULL,
                vtt_data BYTEA NOT NULL
            );
        """)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def save_vtt_as_blob(file_path):
    conn = None
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
                vtt_data BYTEA NOT NULL
            );
        """)

        # --- Read file in binary mode and insert ---
        with open(file_path, 'rb') as f:
            vtt_binary_data = f.read()
        
        cur.execute(
            "INSERT INTO vtt_files (filename, vtt_data) VALUES (%s, %s);",
            (file_path, vtt_binary_data)
        )
        
        conn.commit()
        print(f"Successfully saved '{file_path}' as a BLOB.")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

# --- Example Usage ---
# Create a dummy file first
with open("sample.vtt", "w") as f:
    f.write("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello world.")

save_vtt_as_blob("sample.vtt")