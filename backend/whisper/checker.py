import requests
import psycopg2
import os
from dotenv import load_dotenv, find_dotenv
from krabbler2 import fetch_and_convert
from whisper import transcribeVideoByID
from database import save_vtt_as_blob

# Load the .env file
load_dotenv(find_dotenv())



# --- Database Connection Details ---
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASS = os.environ.get("POSTGRES_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

def getLatestTeletaskID():
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
        print(f"Max teletaskid: {max_id}")
        return max_id

    except (Exception, psycopg2.Error) as error:
        print("Error while querying PostgreSQL", error)
        return -1
    finally:
        if conn:
            cur.close()
            conn.close()

baseurl = "https://www.tele-task.de/lecture/video/"

def checkVideoByID(id):
    url = baseurl+id
    try:
        response = requests.get(url)
        if response.status_code == 404:
            print("404, not available yet")
            return("404")
        elif response.status_code == 401:
            print("not allowed, please use a session cookie")
            return("401")
        elif response.ok:
            print("exists, fetching mp4")
            # run download code
            fetch_and_convert(id)
            # transcribe 
            transcribeVideoByID(id)
            # save to database
            save_vtt_as_blob(id)
            # id should increase by 1
            return("200")

        else:
            print(f"Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error: {e}")


url = "https://www.tele-task.de/lecture/video/"


def checkerLoop():
    #latestID = getLatestTeletaskID()
    latestID = "11401"
    status = checkVideoByID(str(int(latestID)+1))
    while(status == "200"):
        temp = int(latestID) + 1
        latestID=str(temp)
        status = checkVideoByID(baseurl+latestID)

if __name__ == '__main__':
    #checkerLoop()
    id = "11412"
    checkVideoByID(id)

    
    

