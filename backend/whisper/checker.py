import requests
import psycopg2
import os
from dotenv import load_dotenv, find_dotenv

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

def checkLatestVideo(url):

    try:
        response = requests.get(url)
        if response.status_code == 404:
            print("404, not available yet")
            return("404")
        elif response.status_code == 401:
            print("not allowed, please use a session cookie")
            return("401")
        elif response.ok:
            print("exists")
            # run download code
            # save to database
            # id should increase by 1
            return("200")

        else:
            print(f"Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error: {e}")


url = "https://www.tele-task.de/lecture/video/"

if __name__ == '__main__':
    latestID = getLatestTeletaskID()
    #latestID = "11401"
    print(latestID)
    url = baseurl+latestID
    print(url)
    status = checkLatestVideo(url)
    while(status == "200"):
        temp = int(latestID) + 1
        latestID=str(temp)
        status = checkLatestVideo(baseurl+latestID)
    

