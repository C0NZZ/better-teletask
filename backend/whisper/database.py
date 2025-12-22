import psycopg2
from psycopg2 import extensions
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from logger import log

load_dotenv(find_dotenv())

OUTPUTFOLDER = os.environ.get("VTT_DEST_FOLDER")
MODEL = os.environ.get("ASR_MODEL")
COMPUTE_TYPE = os.environ.get("COMPUTE_TYPE")
# print(OUTPUTFOLDER)

script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, OUTPUTFOLDER)

# --- Database Connection Details ---
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASS = os.environ.get("POSTGRES_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")


def initDatabase():
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        print("connected")
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        # TODO Rename: teletaskid to teletask_id, originalLang to original_lang, isOriginalLang to is_original_lang
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS series_data (
                series_id INTEGER PRIMARY KEY,
                series_name VARCHAR(255),
                lecturer_id VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS lecturer_data (
                lecturer_id INTEGER PRIMARY KEY,
                lecturer_name VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS lecture_data (
                teletaskid INTEGER PRIMARY KEY, 
                originalLang VARCHAR(50),
                date DATE,
                lecturer_id INTEGER,
                series_id INTEGER,
                semester VARCHAR(50),
                duration INTERVAL,
                title VARCHAR(255),
                video_mp4 VARCHAR(255),
                desktop_mp4 VARCHAR(255),
                podcast_mp4 VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS vtt_files (
                id SERIAL PRIMARY KEY,
                teletaskid INTEGER NOT NULL,
                language VARCHAR(50) NOT NULL,
                isOriginalLang BOOLEAN NOT NULL,
                vtt_data BYTEA NOT NULL,
                txt_data BYTEA NOT NULL,
                asr_model VARCHAR(255),
                compute_type VARCHAR(255),
                creation_date TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                api_key VARCHAR(255) UNIQUE NOT NULL,
                person_name VARCHAR(255),
                person_email VARCHAR(255),
                creation_date TIMESTAMPTZ DEFAULT NOW(),
                expiration_date TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '3 months'),
                status VARCHAR(255) DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS blacklist_ids (
                teletaskid INTEGER PRIMARY KEY,
                reason VARCHAR(255),
                times_tried INTEGER DEFAULT 1,
                creation_date TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_vtt_files_teletaskid ON vtt_files (teletaskid);
            CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys (api_key);

            """)

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def series_id_exists(series_id):
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute(
            "SELECT COUNT(*) FROM series_data WHERE series_id = %s;",
            (series_id,),
        )
        count = cur.fetchone()[0]
        return count > 0

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def lecturer_id_exists(lecturer_id):
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute(
            "SELECT COUNT(*) FROM lecturer_data WHERE lecturer_id = %s;",
            (lecturer_id,),
        )
        count = cur.fetchone()[0]
        return count > 0

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def add_lecture_data(lecture_data):
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        print(f"Adding lecture data for Teletask ID {lecture_data['teletask_id']}")
        # print(lecture_data)

        teletaskid = lecture_data['teletask_id']
        lecturer_id = lecture_data['lecturer_id']
        lecturer_name = lecture_data['lecturer_name']
        date = lecture_data['date']
        date = datetime.strptime(date, "%B %d, %Y")
        language = lecture_data['language']
        language = "en" if language == "English" else "de"
        duration = lecture_data['duration']
        lecture_title = lecture_data['lecture_title']
        series_id = lecture_data['series_id']
        series_name = lecture_data['series_name']
        url = lecture_data['url']

        # print(date)
        if date.month < 3 or date.month > 10:
            semester = f"WT {date.year-1}/{date.year}"
        else:
            semester = f"ST {date.year}"

        
        if not lecturer_id_exists(lecturer_id):
            cur.execute(
                "INSERT INTO lecturer_data (lecturer_id, lecturer_name) VALUES (%s, %s) ON CONFLICT (lecturer_id) DO NOTHING;",
                (
                    lecturer_id,
                    lecturer_name
                ),
            )
            print(f"Added lecturer data for Lecturer ID {lecturer_id}.")
            conn.commit()
        if not series_id_exists(series_id):
            cur.execute(
                "INSERT INTO series_data (series_id, series_name, lecturer_id) VALUES (%s, %s, %s) ON CONFLICT (series_id) DO NOTHING;",
                (
                    series_id,
                    series_name,
                    lecturer_id
                ),
            )
            print(f"Added series data for Series ID {series_id}.")
            conn.commit()

         
        cur.execute(
            "INSERT INTO lecture_data (teletaskid, originalLang, date, lecturer_id, series_id, semester, duration, title, video_mp4) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
            (
                teletaskid,
                language,
                date,
                lecturer_id,
                series_id,
                semester,
                duration,
                lecture_title,
                url
            ),
        )

        conn.commit()
        print(f"Successfully added lecture data for Teletask ID {teletaskid}.")

    except (psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def get_language_of_lecture(teletaskid) -> str:
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query record ---
        cur.execute(
            "SELECT originalLang FROM lecture_data WHERE teletaskid = %s;",
            (teletaskid,),
        )
        row = cur.fetchone()

        if row:
            return row[0]
        else:
            print(f"No lecture data found for Teletask ID: {teletaskid}")
            return None

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def add_api_key(api_key, person_name, person_email):
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        print(f"Adding API key for {person_name} ({person_email})")

        cur.execute(
            "INSERT INTO api_keys (api_key, person_name, person_email) VALUES (%s, %s, %s) ON CONFLICT (api_key) DO NOTHING;",
            (api_key, person_name, person_email),
        )

        conn.commit()
        print(f"Successfully added API key for {person_name}.")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()


def get_api_key_by_name(person_name):
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query record ---
        cur.execute(
            "SELECT api_key, person_name, person_email, creation_date, expiration_date, status FROM api_keys WHERE person_name = %s;",
            (person_name,),
        )
        rows = cur.fetchall()

        api_key_info = []
        for row in rows:
            api_key_info.append({
                "api_key": row[0],
                "person_name": row[1],
                "person_email": row[2],
                "creation_date": row[3],
                "expiration_date": row[4],
                "status": row[5]
            })
        if api_key_info:
            return api_key_info
        else:
            print(f"No API key found for person name: {person_name}")
            return None

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def get_all_api_keys():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute("SELECT api_key, person_name, person_email, creation_date, expiration_date, status FROM api_keys;")
        rows = cur.fetchall()

        api_keys = []
        for row in rows:
            api_key_info = {
                "api_key": row[0],
                "person_name": row[1],
                "person_email": row[2],
                "creation_date": row[3],
                "expiration_date": row[4],
                "status": row[5]
            }
            api_keys.append(api_key_info)

        return api_keys

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
        return []
    finally:
        if conn:
            cur.close()
            conn.close()

def remove_api_key(api_key):
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        print(f"Removing API key: {api_key}")

        cur.execute(
            "DELETE FROM api_keys WHERE api_key = %s;",
            (api_key,)
        )
        conn.commit()
        print(f"Successfully removed API key: {api_key}")

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

        cur.execute(
            """
            DROP TABLE IF EXISTS "vtt_files";
            DROP TABLE IF EXISTS "lecturer_data";
            DROP TABLE IF EXISTS "series_data";
            DROP TABLE IF EXISTS "lecture_data";
            DROP TABLE IF EXISTS "api_keys";
            DROP TABLE IF EXISTS "blacklist_ids";
        """
        )
        conn.commit()

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def add_id_to_blacklist(teletaskid, reason):
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        print(f"Adding Teletask ID {teletaskid} to blacklist for reason: {reason}")

        cur.execute(
            "INSERT INTO blacklist_ids (teletaskid, reason) VALUES (%s, %s) ON CONFLICT (teletaskid) DO UPDATE SET times_tried = blacklist_ids.times_tried + 1, reason = EXCLUDED.reason;",
            (teletaskid, reason),
        )

        conn.commit()
        print(f"Successfully added Teletask ID {teletaskid} to blacklist.")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def save_vtt_as_blob(teletaskid, language, isOriginalLang):
    conn = None
    file_path = os.path.join(input_path, str(teletaskid) + ".vtt")
    file_path_txt = os.path.join(input_path, str(teletaskid) + ".txt")
    if not os.path.exists(file_path):
        log(
            f"❌ ID: {teletaskid} ERROR: VTT file not found, cant put in database: {file_path}"
        )
        print(
            f"❌ ID: {teletaskid} ERROR: VTT file not found, cant put in database: {file_path}"
        )
        return -1
    if not os.path.exists(file_path_txt):
        log(
            f"❌ ID: {teletaskid} ERROR: TXT file not found, cant put in database: {file_path_txt}"
        )
        print(
            f"❌ ID: {teletaskid} ERROR: TXT file not found, cant put in database: {file_path_txt}"
        )
        return -1
    print(file_path)
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        print(f"Teletask ID: {teletaskid}")
        print(f"Language: {language}")
        print(f"Is Original Language: {isOriginalLang}")

        # --- Read file in binary mode and insert ---
        with open(file_path, "rb") as f:
            vtt_binary_data = f.read()

        with open(file_path_txt, "rb") as f:
            txt_binary_data = f.read()

        cur.execute(
            "INSERT INTO vtt_files (teletaskid,language,isOriginalLang,vtt_data,txt_data,asr_model,compute_type) VALUES (%s,%s,%s,%s,%s,%s,%s);",
            (
                teletaskid,
                language,
                isOriginalLang,
                vtt_binary_data,
                txt_binary_data,
                MODEL,
                COMPUTE_TYPE
            ),
        )

        conn.commit()
        print(f"Successfully saved '{file_path}' as BLOB.\n------------")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()


def getHighestTeletaskID():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute("SELECT MAX(teletaskid) FROM vtt_files;")
        max_id = cur.fetchone()[0]
        print(f"Highest Teletask ID in available in database: {max_id}")
        return max_id

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def getSmallestTeletaskID():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute("SELECT MIN(teletaskid) FROM vtt_files;")
        max_id = cur.fetchone()[0]
        print(f"Smallest Teletask ID in available in database: {max_id}")
        return max_id

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def get_missing_inbetween_ids():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute(""" 
            WITH bounds AS (
            SELECT 
                MIN(teletaskid) AS min_id,
                MAX(teletaskid) AS max_id
            FROM vtt_files
            ),
            all_ids AS (
                SELECT generate_series(
                    (SELECT min_id FROM bounds),
                    (SELECT max_id FROM bounds)
                ) AS teletaskid
            )
            SELECT all_ids.teletaskid
            FROM all_ids
            LEFT JOIN vtt_files vf 
                ON all_ids.teletaskid = vf.teletaskid
            WHERE vf.teletaskid IS NULL
            ORDER BY all_ids.teletaskid;
        """)
        rows = cur.fetchall()
        ids = [row[0] for row in rows]  # extract the first element from each tuple
        # print(ids)
        return ids


    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()
    
def get_blacklisted_ids(): # TODO
     conn = None
     try:
          # --- Connect to PostgreSQL ---
          conn = psycopg2.connect(
                dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
          )
          cur = conn.cursor()
    
          # --- Query all records ---
          cur.execute("SELECT teletaskid FROM blacklist_ids;")
          rows = cur.fetchall()
          ids = [row[0] for row in rows]  # extract the first element from each tuple
          # print(ids)
          return ids
    
     except (Exception, psycopg2.Error) as error:
          print("Error while querying PostgreSQL", error)
          return []
     finally:
          if conn:
                cur.close()
                conn.close()    
    
def get_missing_available_inbetween_ids():
    initial_ids = get_missing_inbetween_ids()
    # print(initial_ids)
    blacklisted_ids = get_blacklisted_ids()
    # print(blacklisted_ids)
    print(list(set(initial_ids) - set(blacklisted_ids)))
    return list(set(initial_ids) - set(blacklisted_ids))


def get_missing_translations():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute(""" 
            WITH all_ids AS( SELECT DISTINCT teletaskid FROM vtt_files )
            SELECT teletaskid, language FROM vtt_files
            WHERE isOriginalLang = False
            ORDER BY teletaskid DESC;
        """)
        rows = cur.fetchall()
        id_lang_pairs = [(row[0],row[1]) for row in rows]  # extract the first element from each tuple
        # print(id_lang_pairs)


    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
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
        cur.execute(
            "SELECT id, teletaskid, language,isOriginalLang, vtt_data, txt_data, compute_type FROM vtt_files ORDER BY id;"
        )
        rows = cur.fetchall()

        print(f"\n=== Found {len(rows)} VTT file(s) in database ===\n")

        for row in rows:
            record_id, teletaskid, language, isOriginalLang, vtt_data, txt_data, compute_type = (
                row
            )
            print(f"--- Record ID: {record_id} ---")
            print(f"Teletask ID: {teletaskid}")
            print(f"Language: {language}")
            print(f"Is Original Language: {isOriginalLang}")
            print(f"VTT Data (size): {len(vtt_data)} bytes")
            print(f"Compute Type: {compute_type}")
            print(f"VTT Content:")
            print("-" * 50)
            # Convert memoryview to bytes, then decode to string for display
            
            try:
                vtt_bytes = bytes(vtt_data)
                vtt_content = vtt_bytes.decode("utf-8")
                print(vtt_content)

                txt_bytes = bytes(txt_data)
                txt_content = txt_bytes.decode("utf-8")
                print(txt_content)
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

def original_language_exists(teletaskid):
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute(
            "SELECT COUNT(*) FROM vtt_files WHERE teletaskid = %s AND isOriginalLang = TRUE;",
            (teletaskid,),
        )
        count = cur.fetchone()[0]
        return count > 0

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def databaseTestScript():
    # --- Example Usage ---
    # Create a dummy file first
    with open("sample.vtt", "w") as f:
        f.write("WEBVTT\n\n00:00:01.000 --> 00:00:14.000\nHello world.")
    initDatabase()
    save_vtt_as_blob("1", "de", True)

    # Query and print all blobs
    get_all_vtt_blobs()


if __name__ == "__main__":
    clearDatabase()
    initDatabase()
    #print(get_language_of_lecture(11516))
    #save_vtt_as_blob(11408, "de", True)
    #save_vtt_as_blob(11408, "en", False)
    #save_vtt_as_blob(11402, "de", True)
    #save_vtt_as_blob(11402, "en", False)
    #add_id_to_blacklist(11406, "404")
    #get_all_vtt_blobs()
    #get_all_vtt_blobs()
    # databaseTestScript()
    #getHighestTeletaskID()
    #getSmallestTeletaskID()
    #get_missing_inbetween_ids()
    #get_missing_translations()
    #get_missing_available_ids()
    #print(original_language_exists(11409))