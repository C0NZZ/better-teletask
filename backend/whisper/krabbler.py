import re
import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
import ffmpeg
import os
from datetime import datetime
from logger import log
from dotenv import load_dotenv, find_dotenv
from database import get_language_of_lecture, getHighestTeletaskID, save_vtt_as_blob, add_lecture_data
from whisper import transcribeVideoByID

load_dotenv(find_dotenv())

OUTPUTFOLDER = os.environ.get("VTT_DEST_FOLDER")
INPUTFOLDER = os.environ.get("RECORDING_SOURCE_FOLDER")
USERNAME_COOKIE = os.environ.get("USERNAME_COOKIE")
# print(OUTPUTFOLDER)
# print(INPUTFOLDER)
# print(USERNAME_COOKIE)

script_dir = os.path.dirname(os.path.abspath(__file__))
baseinput =  os.path.join(script_dir, INPUTFOLDER)
baseoutput =  os.path.join(script_dir, OUTPUTFOLDER)
baseurl = "https://www.tele-task.de/lecture/video/"
print("Base input folder: "+baseinput)
print("Base output folder: "+baseoutput)

testid = 11413

def fetchMP4(id, response) -> str:
    soup = BeautifulSoup(response.text, "html.parser")
    player = soup.find(id="player")

    if player and player.has_attr("configuration"):
        config_json = player["configuration"]
        #print(config_json)

        print("Trying to fetch podcast.mp4 from fallbackStreams")
        try:
            # TODO ADD LOGGING
            config = json.loads(config_json)
            fallbackStreams = config.get("fallbackStream")
            if fallbackStreams is not None:
                #print (fallbackStreams)
               
                for key, url in fallbackStreams.items():
                        if url and url.endswith('podcast.mp4'):
                            print(f"Found first podcast.mp4 from FallbackStream URL: {url}")
                            return url
            
                for key, url in fallbackStreams.items():
                        if url and url.endswith('.mp4'):
                            print(f"Found .mp4 URL from FallbackStream: {url}")
                            return url
                
                    
            else:
                print("'fallbackStreams' key not found in configuration.")
        except json.JSONDecodeError:
            print("Configuration attribute is not valid JSON:")
            print(config_json)

        print("did not find podcast.mp4 in fallbackStreams")
        print("Trying to fetch .mp4 from streams")
        try:
            # TODO ADD LOGGING
            config = json.loads(config_json)
            streams = config.get("streams")
            if streams is not None:
                #print (streams)
                for stream in streams:
                    for key, url in stream.items():
                        if url and url.endswith('podcast.mp4'):
                            print(f"Found first .mp4 URL: {url}")
                            return url
                sd_urls = [stream.get("sd") for stream in streams if "sd" in stream]
                print("SD URLs:")
                for url in sd_urls:
                    if url.endswith("video.mp4") or url.endswith("CameraMicrophone.mp4"):
                        print(url)
                        return url
                for url in sd_urls:
                    if url.endswith(".mp4"):
                        print(url)
                        return url
                for stream in streams:
                    for key, url in stream.items():
                        if url and url.endswith('.mp4'):
                            print(f"Found first .mp4 URL: {url}")
                            return url
                    
            else:
                print("'streams' key not found in configuration.")
        except json.JSONDecodeError:
            print("Configuration attribute is not valid JSON:")
            print(config_json)
    else:
        print("Element with id 'player' and attribute 'configuration' not found.")

    print("No mp4 URL found")
    return ""

def pingVideoByID(id) -> str:
    url = baseurl+id
    cookies = {"username": USERNAME_COOKIE}
    try:
        print("requesting "+url)
        response = requests.get(url, cookies=cookies, verify='chain.pem')
        if(response.status_code == 200):
            print("200, Video exists")
            return "200"
        elif(response.status_code == 404): # literally does not exist
            print("404, not available yet")
            return "404"
        elif(response.status_code == 401):
            print("401, not allowed, please use a session cookie")
            return "401"
        elif(response.status_code == 403): # these can happen randomly
            print("403, access forbidden")
            return "403"
    except requests.ConnectionError as e:
        print(f"Error fetching video: {e}")
        return ""

def get_upper_ids():
    ids = []
    unreachable_ids = []
    highest = getHighestTeletaskID()
    if highest is None:
        return ids
    highest = highest + 1
    for i in range(10):
        res = pingVideoByID(str(highest + i))
        if res == "200":
            ids.append(highest+i)
            if unreachable_ids:
                print("Unreachable IDs found:")
                for uid in unreachable_ids:
                    print(f" - {uid}")
                    # TODO log 
        if res == "401":
            #need to handle that case, because then we have no cookie
            print()
        if res == "403" or res =="404":
            #need special logging if a id is 403 or 404 but after that its 200
            unreachable_ids.append(res)
    return ids
    
def downloadMP4(url, id):
    print(f"Downloading: {url}")
    try:
        mp4_response = requests.get(url, stream=True, verify='chain.pem')
        mp4_response.raise_for_status()
        total_size = int(mp4_response.headers.get('content-length', 0))
        with open(baseinput+str(id)+".mp4", "wb") as f, tqdm(
            desc="Downloading "+baseinput+str(id)+".mp4",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in mp4_response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
        print("Download complete:"+baseinput+str(id)+".mp4")
    except Exception as e:
        print("Error downloading MP4:", e)
        raise

def convert_to_mp3(source, out_mp3):
    """Convert a source (URL or local file) to MP3 using ffmpeg-python.

    This requires ffmpeg to be available on the system.
    """
    try:
        (
            ffmpeg.input(source)
            .output(
                out_mp3,
                format='mp3',
                acodec='libmp3lame',
                **{"q:a": 2},
                vn=None
            )
            .overwrite_output()
            .global_args('-hide_banner', '-loglevel', 'error')
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f'Saved MP3 to {out_mp3}')
    except ffmpeg.Error as e:
        err = e.stderr.decode() if getattr(e, 'stderr', None) else str(e)
        log(f"❌ ERROR converting to MP3: {err}")
        print('ffmpeg error:\n', err)
        raise



def transcribePipelineVideoByID(id):
    url = fetchLecture(str(id))
    if url == "":
        print("No mp4 URL found, cannot transcribe")
        return -1
    else:
        try:
            convert_to_mp3(url, baseinput+str(id)+".mp3")
        except Exception as e:
            print("Error converting to mp3:", e)
            print("Trying to download mp4 and convert locally")
            try:
                downloadMP4(url, id)
                convert_to_mp3(baseinput+str(id)+".mp4", baseinput+str(id)+".mp3")
            except Exception as e2:
                print("Error downloading and converting locally:", e2)
                log(f"❌ ID: {id} ERROR: Could not convert video to mp3.")
                return -1

        try:
            language = transcribeVideoByID(str(id))
        except Exception as e:
            print("Error transcribing video:", e)
            log(f"❌ ID: {id} ERROR: Could not transcribe video.")
            return -1
        
        try:
            save_vtt_as_blob(id,language,True)
        except Exception as e:
            print("Error saving VTT to database:", e)
            log(f"❌ ID: {id} ERROR: Could not save VTT to database.")
            return -1
        
        log(f"✅ ID: {id} Transcription and saving completed successfully.")
        return 0


def fetchLecture(id) -> str:
    cookies = {"username": USERNAME_COOKIE}
    url = baseurl + id
    print("requesting "+url)
    response = requests.get(url, cookies=cookies, verify='chain.pem')
    response.raise_for_status()

    url = fetchMP4(id, response)
    if get_language_of_lecture(id) is None:
        print("Fetching lecturer data for ID "+id)
        log("Fetching lecturer data for ID "+id)
        getLecturerData(id, response, url)
    else:
        print("Lecturer data already exists for ID "+id)
        log("Lecturer data already exists for ID "+id)
    return url

# TODO crawl lecturer data of existing vtts without one
def getLecturerData(id, response, url):
    """
    Input: a BeautifulSoup Tag for the <div class="box"> or a string containing that HTML.
    Returns: dict with keys:
      - lecturer_id (str or None)
      - lecturer_name (str or None)
      - date (str or None)
      - language (str or None)
      - duration (str or None)
      - title (lecture name) (str or None)
      - series_id (str or None)
      - series_name (str or None)
    """
    
    url = baseurl+id
    cookies = {"username": USERNAME_COOKIE}
    try:
        print("requesting "+url)
        response = requests.get(url, cookies=cookies, verify='chain.pem')
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        lecture_info_div = soup.find("img", class_="box nopad lecture-img").parent
        if lecture_info_div:
            
            lecturer_name = lecture_info_div.get_text()
            
            # print(lecture_info_div)

            # print("------------")
            lecture_name= lecture_info_div.find("h3").get_text()
            print("Lecture Name: " + lecture_name)
            h5 = lecture_info_div.find("h5")
            if h5:
                a = h5.find("a", href=True)
                if a:
                    series_name = a.get_text(strip=True)
                    m = re.search(r"/series/(\d+)", a["href"])
                    series_id = m.group(1) if m else None
                    print("Series Name: " + series_name)
                    print("Series ID: " + series_id)


            lect_a = lecture_info_div.find("a", href=re.compile(r"^/lecturer/"))
            if lect_a:
                lecturer_name = lect_a.get_text(strip=True)
                m = re.search(r"/lecturer/(\d+)", lect_a["href"])
                lecturer_id = m.group(1) if m else None
                print("Lecturer Name: " + lecturer_name)
                print("Lecturer ID: " + lecturer_id)


            inner = lecture_info_div.decode_contents()

            def find_field(label):
                # match 'Label: ... <br' and capture the ... part
                m = re.search(rf"{re.escape(label)}:\s*(.*?)\s*<br", inner, re.I | re.S)
                return m.group(1).strip() if m else None
            
            date = find_field("Date")
            language = find_field("Language")
            duration = find_field("Duration")

            print("Date: " + (date))
            print("Language: " + (language))
            print("Duration: " + (duration))

            #print(datetime.strptime(date, "%B %d, %Y"))

            lecture_data = {
                "teletask_id": id,
                "lecturer_id": lecturer_id,
                "lecturer_name": lecturer_name,
                "date": date,
                "language": language,
                "duration": duration,
                "lecture_title": lecture_name,
                "series_id": series_id,
                "series_name": series_name,
                "url": url
            }
            add_lecture_data(lecture_data)

            return 
        else:
            print("Lecturer name not found.")
            return 
    except requests.RequestException as e:
        print(f"Error fetching lecturer data: {e}")
        return 
    

if __name__ == '__main__':
    #pingVideoByID(str(2110))
    #transcribePipelineVideoByID(str(testid))
    #transcribePipelineVideoByID(str(11519))
    #getLecturerData(str(11516))
    fetchLecture(str(11519))
