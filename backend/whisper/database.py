import psycopg2
from psycopg2 import extensions
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from models import VttFile, VttLine, ApiKey, LectureData, SeriesData, LecturerData, BlacklistEntry, SearchResult

# setup logging
import logger
import logging
logger = logging.getLogger("btt_root_logger")

load_dotenv(find_dotenv())

OUTPUTFOLDER = os.environ.get("VTT_DEST_FOLDER")
MODEL = os.environ.get("ASR_MODEL")
COMPUTE_TYPE = os.environ.get("COMPUTE_TYPE")


script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, OUTPUTFOLDER)

# --- Database Connection Details ---
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASS = os.environ.get("POSTGRES_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")


def initDatabase():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        logger.info("Initialized database connection.")
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur.execute(
            """
            CREATE EXTENSION IF NOT EXISTS pg_trgm;

            CREATE TABLE IF NOT EXISTS series_data (
                series_id INTEGER PRIMARY KEY,
                series_name VARCHAR(255),
                lecturer_ids INTEGER[]
            );
            CREATE TABLE IF NOT EXISTS lecturer_data (
                lecturer_id INTEGER PRIMARY KEY,
                lecturer_name VARCHAR(255) NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lecture_data (
                lecture_id INTEGER PRIMARY KEY, 
                language VARCHAR(50),
                date DATE,
                lecturer_ids INTEGER[],
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
                lecture_id INTEGER NOT NULL,
                language VARCHAR(50) NOT NULL,
                is_original_lang BOOLEAN NOT NULL,
                vtt_data BYTEA NOT NULL,
                txt_data BYTEA NOT NULL,
                asr_model VARCHAR(255),
                compute_type VARCHAR(255),
                creation_date TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS vtt_lines (
                id BIGSERIAL PRIMARY KEY,
                vtt_file_id INTEGER NOT NULL REFERENCES vtt_files(id) ON DELETE CASCADE,
                series_id INTEGER NOT NULL REFERENCES series_data(series_id) ON DELETE CASCADE,
                language VARCHAR(50) NOT NULL,
                lecturer_ids INTEGER[] NOT NULL,
                line_number INTEGER NOT NULL,
                ts_start INTEGER NOT NULL,
                ts_end INTEGER NOT NULL,
                content TEXT NOT NULL
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
                lecture_id INTEGER PRIMARY KEY,
                reason VARCHAR(255),
                times_tried INTEGER DEFAULT 1,
                creation_date TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_vtt_files_lecture_id ON vtt_files (lecture_id);
            CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys (api_key);

            CREATE INDEX IF NOT EXISTS idx_lines_trgm ON vtt_lines USING gin (content gin_trgm_ops);
            CREATE INDEX IF NOT EXISTS idx_lines_series_id ON vtt_lines (series_id);
            CREATE INDEX IF NOT EXISTS idx_lines_lecture_id ON vtt_lines (vtt_file_id);
            CREATE INDEX IF NOT EXISTS idx_lines_language ON vtt_lines (language);

            """)

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def get_series_of_vtt_file(vtt_file_id) -> SeriesData | None:
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.series_id, s.series_name, s.lecturer_ids
            FROM vtt_files vf
            JOIN lecture_data ld ON vf.lecture_id = ld.lecture_id
            JOIN series_data s ON ld.series_id = s.series_id
            WHERE vf.id = %s;
            """,
            (vtt_file_id,),
        )
        row = cur.fetchone()
        if row:
            return SeriesData(
                series_id=row[0],
                series_name=row[1],
                lecturer_ids=row[2],
            )
        logger.info(f"No series found for VTT file ID: {vtt_file_id}")
        return None
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def get_all_lecture_ids():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute("SELECT lecture_id FROM lecture_data;")
        rows = cur.fetchall()
        ids = [row[0] for row in rows]  # extract the first element from each tuple
        logger.debug(f"Fetched all lecture IDs: {ids}")
        return ids

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
        return []
    finally:
        if conn:
            cur.close()
            conn.close()

def get_all_original_vtt_ids():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Query all records ---
        cur.execute("SELECT lecture_id FROM vtt_files WHERE is_original_lang = TRUE;")
        rows = cur.fetchall()
        ids = [row[0] for row in rows]  # extract the first element from each tuple
        logger.debug(f"Fetched all original VTT IDs: {ids}")
        return ids

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
        return []
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
        logger.error("Error while querying PostgreSQL", error)
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
        logger.error("Error while querying PostgreSQL", error)
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

        teletaskid = lecture_data['lecture_id']
        lecturer_ids = lecture_data['lecturer_ids']
        lecturer_names = lecture_data['lecturer_names']
        date = lecture_data['date']
        date = datetime.strptime(date, "%B %d, %Y")
        language = lecture_data['language']
        language = "en" if language == "English" else "de"
        duration = lecture_data['duration']
        lecture_title = lecture_data['lecture_title']
        series_id = lecture_data['series_id']
        series_name = lecture_data['series_name']
        url = lecture_data['url']

        if date.month < 3 or date.month > 10:
            semester = f"WT {date.year-1}/{date.year}"
        else:
            semester = f"ST {date.year}"

        for lecturer_id in lecturer_ids:
            if not lecturer_id_exists(lecturer_id):
                cur.execute(
                    "INSERT INTO lecturer_data (lecturer_id, lecturer_name) VALUES (%s, %s) ON CONFLICT (lecturer_id) DO NOTHING;",
                    (
                        lecturer_id,
                        lecturer_names[lecturer_ids.index(lecturer_id)]
                    ),
                )
                logger.info(f"Added lecturer data for Lecturer ID {lecturer_id}.", extra={'id': teletaskid})
                conn.commit()

        
        if not series_id_exists(series_id):
            cur.execute(
                "INSERT INTO series_data (series_id, series_name, lecturer_ids) VALUES (%s, %s, %s::INTEGER[]) ON CONFLICT (series_id) DO NOTHING;",
                (
                    series_id,
                    series_name,
                    lecturer_ids
                ),
            )
            logger.info(f"Added series data for Series ID {series_id}.", extra={'id': teletaskid})
            conn.commit()
        else:
            cur.execute(
                "UPDATE series_data SET lecturer_ids = array(SELECT DISTINCT unnest(lecturer_ids || CAST(%s AS INTEGER[]))) WHERE series_id = %s;",
                (
                    lecturer_ids,
                    series_id
                ),
            )
            logger.info(f"Updated lecturer IDs for Series ID {series_id}.", extra={'id': teletaskid})
            conn.commit()
                

        cur.execute(
            "INSERT INTO lecture_data (lecture_id, language, date, lecturer_ids, series_id, semester, duration, title, video_mp4) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
            (
                teletaskid,
                language,
                date,
                lecturer_ids,
                series_id,
                semester,
                duration,
                lecture_title,
                url
            ),
        )

        conn.commit()

    except (psycopg2.Error) as error:
        logger.error("Error while connecting to PostgreSQL", error)
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
            "SELECT language FROM lecture_data WHERE lecture_id = %s;",
            (teletaskid,),
        )
        row = cur.fetchone()

        if row:
            return row[0]
        else:
            logger.info(f"No lecture data found for Teletask ID: {teletaskid}")
            return None

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
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


        cur.execute(
            "INSERT INTO api_keys (api_key, person_name, person_email) VALUES (%s, %s, %s) ON CONFLICT (api_key) DO NOTHING;",
            (api_key, person_name, person_email),
        )

        conn.commit()

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()


def get_api_key_by_key(api_key) -> ApiKey | None:
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT api_key, person_name, person_email, creation_date, expiration_date, status FROM api_keys WHERE api_key = %s;",
            (api_key,),
        )
        row = cur.fetchone()

        if row:
            return ApiKey(
                api_key=row[0],
                person_name=row[1],
                person_email=row[2],
                creation_date=row[3],
                expiration_date=row[4],
                status=row[5],
            )
        else:
            logger.info(f"No API key found: {api_key}")
            return None

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
        return None
    finally:
        if conn:
            cur.close()
            conn.close()


def get_api_key_by_name(person_name) -> list[ApiKey] | None:
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT api_key, person_name, person_email, creation_date, expiration_date, status FROM api_keys WHERE person_name = %s;",
            (person_name,),
        )
        rows = cur.fetchall()

        api_keys = [
            ApiKey(
                api_key=row[0],
                person_name=row[1],
                person_email=row[2],
                creation_date=row[3],
                expiration_date=row[4],
                status=row[5],
            )
            for row in rows
        ]
        if api_keys:
            return api_keys
        else:
            logger.info(f"No API key found for person name: {person_name}")
            return None

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def get_all_api_keys() -> list[ApiKey]:
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT api_key, person_name, person_email, creation_date, expiration_date, status FROM api_keys;")
        rows = cur.fetchall()

        return [
            ApiKey(
                api_key=row[0],
                person_name=row[1],
                person_email=row[2],
                creation_date=row[3],
                expiration_date=row[4],
                status=row[5],
            )
            for row in rows
        ]

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
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

        cur.execute(
            "DELETE FROM api_keys WHERE api_key = %s;",
            (api_key,)
        )
        conn.commit()
        logger.info(f"Successfully removed API key: {api_key}")
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def clearDatabase():
    conn = None
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        conn.autocommit = False
        cur = conn.cursor()

        cur.execute(
            """
            DROP TABLE IF EXISTS "vtt_lines";
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
        logger.error("Error while connecting to PostgreSQL", error)
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

        cur.execute(
            "INSERT INTO blacklist_ids (lecture_id, reason) VALUES (%s, %s) ON CONFLICT (lecture_id) DO UPDATE SET times_tried = blacklist_ids.times_tried + 1, reason = EXCLUDED.reason;",
            (teletaskid, reason),
        )

        conn.commit()
        logger.info(f"Successfully added Teletask ID {teletaskid} to blacklist.")

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def save_vtt_as_blob(teletaskid, language, isOriginalLang):
    conn = None
    file_path = os.path.join(input_path, str(teletaskid) + ".vtt")
    file_path_txt = os.path.join(input_path, str(teletaskid) + ".txt")
    if not os.path.exists(file_path):
        logger.error(f"VTT file not found, cant put in database: {file_path}", extra={'id': teletaskid})
        return -1
    if not os.path.exists(file_path_txt):
        logger.error(f"TXT file not found, cant put in database: {file_path_txt}", extra={'id': teletaskid})
        return -1
    try:
        # --- Connect to PostgreSQL ---
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        # --- Read file in binary mode and insert ---
        with open(file_path, "rb") as f:
            vtt_binary_data = f.read()

        with open(file_path_txt, "rb") as f:
            txt_binary_data = f.read()

        cur.execute(
            "INSERT INTO vtt_files (lecture_id, language, is_original_lang, vtt_data, txt_data, asr_model, compute_type) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id;",
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

        vtt_file_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Successfully saved '{file_path}' as BLOB", extra={'id': teletaskid})
        return vtt_file_id
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while connecting to PostgreSQL", error)
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
        cur.execute("SELECT MAX(lecture_id) FROM vtt_files;")
        max_id = cur.fetchone()[0]
        logger.info(f"Highest Teletask ID in available in database: {max_id}")
        return max_id

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
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
        cur.execute("SELECT MIN(lecture_id) FROM vtt_files;")
        max_id = cur.fetchone()[0]
        logger.info(f"Smallest Teletask ID in available in database: {max_id}")
        return max_id

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
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
                MIN(lecture_id) AS min_id,
                MAX(lecture_id) AS max_id
            FROM vtt_files
            ),
            all_ids AS (
                SELECT generate_series(
                    (SELECT min_id FROM bounds),
                    (SELECT max_id FROM bounds)
                ) AS lecture_id
            )
            SELECT all_ids.lecture_id
            FROM all_ids
            LEFT JOIN vtt_files vf 
                ON all_ids.lecture_id = vf.lecture_id
            WHERE vf.lecture_id IS NULL
            ORDER BY all_ids.lecture_id;
        """)
        rows = cur.fetchall()
        ids = [row[0] for row in rows]  # extract the first element from each tuple
        return ids


    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
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
          cur.execute("SELECT lecture_id FROM blacklist_ids;")
          rows = cur.fetchall()
          ids = [row[0] for row in rows]  # extract the first element from each tuple
          return ids
    
     except (Exception, psycopg2.Error) as error:
          logger.error("Error while querying PostgreSQL", error)
          return []
     finally:
          if conn:
                cur.close()
                conn.close()    
    
def get_missing_available_inbetween_ids():
    initial_ids = get_missing_inbetween_ids()
    blacklisted_ids = get_blacklisted_ids()
    logger.debug(list(set(initial_ids) - set(blacklisted_ids)))
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
            WITH all_ids AS( SELECT DISTINCT lecture_id FROM vtt_files )
            SELECT lecture_id, language FROM vtt_files
            WHERE is_original_lang = False
            ORDER BY lecture_id DESC;
        """)
        rows = cur.fetchall()
        id_lang_pairs = [(row[0],row[1]) for row in rows]  # extract the first element from each tuple
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def bulk_insert_vtt_lines(vtt_lines: list[VttLine]):
    if not vtt_lines:
        return
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        values = [
            (line.vtt_file_id, line.series_id, line.language, line.lecturer_ids, line.line_number, line.ts_start, line.ts_end, line.content)
            for line in vtt_lines
        ]
        execute_values(
            cur,
            "INSERT INTO vtt_lines (vtt_file_id, series_id, language, lecturer_ids, line_number, ts_start, ts_end, content) VALUES %s",
            values,
            page_size=1000
        )
        conn.commit()
        logger.info(f"Bulk inserted {len(vtt_lines)} VTT lines.")
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while bulk inserting VTT lines", error)
    finally:
        if conn:
            cur.close()
            conn.close()

def search_vtt_lines(
    query: str,
    series_id: int | None = None,
    language: str | None = None,
    lecturer_id: int | None = None,
    lecture_id: int | None = None,
    threshold: float = 0.15,
    limit: int = 20,
) -> list[SearchResult]:
    """Fuzzy search vtt_lines using pg_trgm similarity.

    Optional filters:
        series_id   - restrict to a specific series
        language     - restrict to a language (e.g. 'en', 'de')
        lecturer_id  - restrict to lines whose lecturer_ids array contains this id
        lecture_id   - restrict to a specific lecture (via vtt_files)
        threshold    - minimum similarity score (0-1, lower = more results)
        limit        - max rows returned
    """
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        filters = ["similarity(vl.content, %s) >= %s"]
        params: list = [query, threshold]

        if series_id is not None:
            filters.append("vl.series_id = %s")
            params.append(series_id)

        if language is not None:
            filters.append("vl.language = %s")
            params.append(language)

        if lecturer_id is not None:
            filters.append("%s = ANY(vl.lecturer_ids)")
            params.append(lecturer_id)

        if lecture_id is not None:
            filters.append("vf.lecture_id = %s")
            params.append(lecture_id)

        where = " AND ".join(filters)
        params.append(limit)

        sql = f"""
            SELECT
                vl.vtt_file_id,
                vf.lecture_id,
                vl.series_id,
                sd.series_name,
                vl.language,
                vl.line_number,
                vl.ts_start,
                vl.ts_end,
                vl.content,
                similarity(vl.content, %s) AS similarity
            FROM vtt_lines vl
            JOIN vtt_files vf   ON vf.id = vl.vtt_file_id
            JOIN series_data sd ON sd.series_id = vl.series_id
            WHERE {where}
            ORDER BY similarity DESC
            LIMIT %s
        """

        # The first %s in the SELECT is for similarity(); prepend query again
        cur.execute(sql, [query] + params)
        rows = cur.fetchall()

        return [
            SearchResult(
                vtt_file_id=row[0],
                lecture_id=row[1],
                series_id=row[2],
                series_name=row[3],
                language=row[4],
                line_number=row[5],
                ts_start=row[6],
                ts_end=row[7],
                content=row[8],
                similarity=row[9],
            )
            for row in rows
        ]
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while searching VTT lines", error)
        return []
    finally:
        if conn:
            cur.close()
            conn.close()

def get_vtt_file_by_id(vtt_file_id) -> VttFile | None:
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT id, lecture_id, language, is_original_lang, vtt_data, txt_data, asr_model, compute_type, creation_date FROM vtt_files WHERE id = %s;",
            (vtt_file_id,),
        )
        row = cur.fetchone()
        if row:
            return VttFile(
                id=row[0],
                lecture_id=row[1],
                language=row[2],
                is_original_lang=row[3],
                vtt_data=bytes(row[4]),
                txt_data=bytes(row[5]),
                asr_model=row[6],
                compute_type=row[7],
                creation_date=row[8],
            )
        logger.info(f"No VTT file found with ID: {vtt_file_id}")
        return None
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def get_vtt_files_by_lecture_id(lecture_id) -> list[VttFile]:
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT id, lecture_id, language, is_original_lang, vtt_data, txt_data, asr_model, compute_type, creation_date FROM vtt_files WHERE lecture_id = %s;",
            (lecture_id,),
        )
        rows = cur.fetchall()
        return [
            VttFile(
                id=row[0],
                lecture_id=row[1],
                language=row[2],
                is_original_lang=row[3],
                vtt_data=bytes(row[4]),
                txt_data=bytes(row[5]),
                asr_model=row[6],
                compute_type=row[7],
                creation_date=row[8],
            )
            for row in rows
        ]
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
        return []
    finally:
        if conn:
            cur.close()
            conn.close()

def get_all_vtt_blobs() -> list[VttFile]:
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT id, lecture_id, language, is_original_lang, vtt_data, txt_data, asr_model, compute_type, creation_date FROM vtt_files ORDER BY id;"
        )
        rows = cur.fetchall()
        logger.info(f"Retrieved {len(rows)} VTT file(s) from database.")
        return [
            VttFile(
                id=row[0],
                lecture_id=row[1],
                language=row[2],
                is_original_lang=row[3],
                vtt_data=bytes(row[4]),
                txt_data=bytes(row[5]),
                asr_model=row[6],
                compute_type=row[7],
                creation_date=row[8],
            )
            for row in rows
        ]
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
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
            "SELECT COUNT(*) FROM vtt_files WHERE lecture_id = %s AND is_original_lang = TRUE;",
            (teletaskid,),
        )
        count = cur.fetchone()[0]
        return count > 0

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while querying PostgreSQL", error)
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
    from kratzer import fetchLecture
    clearDatabase()
    initDatabase()
    #print(get_language_of_lecture(11516))
    save_vtt_as_blob(11408, "de", True)
    save_vtt_as_blob(11412, "de", True)
    save_vtt_as_blob(11413, "de", True)
    fetchLecture(11408)
    fetchLecture(11412)
    fetchLecture(11413)
    #get_all_vtt_blobs()
    #save_vtt_as_blob(11406, "de", True)
    #save_vtt_as_blob(11405, "de", True)
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
