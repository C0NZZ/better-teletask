import re
import requests
from requests.models import Response, HTTPError
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
import ffmpeg
import os
from dotenv import load_dotenv, find_dotenv
from database import get_language_of_lecture, getHighestTeletaskID, save_vtt_as_blob, add_lecture_data

# setup logging
import logger
import logging
logger = logging.getLogger("btt_root_logger")

load_dotenv(find_dotenv())

OUTPUTFOLDER = os.environ.get("VTT_DEST_FOLDER")
INPUTFOLDER = os.environ.get("RECORDING_SOURCE_FOLDER")
USERNAME_COOKIE = os.environ.get("USERNAME_COOKIE")
script_dir = os.path.dirname(os.path.abspath(__file__))
baseinput =  os.path.join(script_dir, INPUTFOLDER)
baseoutput =  os.path.join(script_dir, OUTPUTFOLDER)
baseurl = "https://www.tele-task.de/lecture/video/"

logger.debug("output folder: "+OUTPUTFOLDER)
logger.debug("input folder: "+INPUTFOLDER)
logger.debug("username cookie: "+USERNAME_COOKIE)
logger.debug("base input folder: "+baseinput)
logger.debug("base output folder: "+baseoutput)


def fetchBody(id) -> Response:
    cookies = {"username": USERNAME_COOKIE}
    url = baseurl + id
    logger.info("requesting "+url, extra={'id': id})
    response = requests.get(url, cookies=cookies, verify='chain.pem')
    response.raise_for_status()
    return response

def fetchMP4(id, response) -> str:
    soup = BeautifulSoup(response.text, "html.parser")
    player = soup.find(id="player")

    if player and player.has_attr("configuration"):
        config_json = player["configuration"]
        logger.debug("Trying to fetch podcast.mp4 from fallbackStreams for ID ", extra={'id': id})
        try:

            config = json.loads(config_json)
            fallbackStreams = config.get("fallbackStream")
            if fallbackStreams is not None:               
                for key, url in fallbackStreams.items():
                        if url and url.endswith('podcast.mp4'):
                            logger.info(f"Found first podcast.mp4 from FallbackStream URL: {url}", extra={'id': id})
                            return url
            
                for key, url in fallbackStreams.items():
                        if url and url.endswith('.mp4'):
                            logger.info(f"Found .mp4 URL from FallbackStream: {url}", extra={'id': id})
                            return url
                
                    
            else:
                logger.info("'fallbackStreams' key not found in configuration.", extra={'id': id})
        except json.JSONDecodeError:
            logger.error("Configuration attribute is not valid JSON:", extra={'id': id})
            logger.error(config_json, extra={'id': id})

        logger.info("did not find podcast.mp4 in fallbackStreams, trying to fetch .mp4 from streams", extra={'id': id})

        try:
            config = json.loads(config_json)
            streams = config.get("streams")
            if streams is not None:
                for stream in streams:
                    for key, url in stream.items():
                        if url and url.endswith('podcast.mp4'):
                            logger.info(f"Found podcast.mp4 URL in streams: {url}", extra={'id': id})
                            return url
                sd_urls = [stream.get("sd") for stream in streams if "sd" in stream]
            
                for url in sd_urls:
                    if url.endswith("video.mp4") or url.endswith("CameraMicrophone.mp4") or url.endswith("video_complete.mp4"):
                        logger.info(f"Found video.mp4 URL in sd streams: {url}", extra={'id': id})
                        return url
                for url in sd_urls:
                    if url.endswith(".mp4"):
                        logger.info(f"Found first .mp4 URL in sd streams: {url}", extra={'id': id})
                        return url
                for stream in streams:
                    for key, url in stream.items():
                        if url and url.endswith('.mp4'):
                            logger.info(f"Found first .mp4 URL in streams: {url}", extra={'id': id})
                            return url
                    
            else:
                logger.warning("'streams' key not found in configuration.", extra={'id': id})
        except json.JSONDecodeError:
            logger.error(f"Configuration attribute is not valid JSON: {config_json}", extra={'id': id})
    else:
        logger.error("Element with id 'player' and attribute 'configuration' not found, cant find mp4 URL", extra={'id': id})

    logger.error("No mp4 URL found", extra={'id': id})
    return ""

def pingVideoByID(id) -> str:
    try: 
        response = fetchBody(id)
    except HTTPError as e:
        logger.error("Error fetching body:", extra={'id': id})
        return ""
    if(response.status_code == 200):
        logging.info("Code 200, Video exists", extra={'id': id})
        return "200"
    elif(response.status_code == 404): # literally does not exist
        logging.info("Code 404, not available yet", extra={'id': id})
        return "404"
    elif(response.status_code == 401):
        logging.info("Code 401, not allowed, please use a session cookie", extra={'id': id})
        global USERNAME_COOKIE
        USERNAME_COOKIE = os.environ.get("USERNAME_COOKIE")
        return "401"
    elif(response.status_code == 403): # these can happen randomly
        logging.info("Code 403, access forbidden", extra={'id': id})
        return "403"


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
        if res == "401":
            logger.error("Received 401 Unauthorized. Check your USERNAME_COOKIE environment variable.", extra={'id': highest + i})
            #need to handle that case, because then we have no cookie
        if res == "403" or res =="404":
            logger.warning(f"Received {res} for ID {highest + i}.", extra={'id': highest + i})
            unreachable_ids.append(res)
    return ids
    
def downloadMP4(url, id):
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
        logging.info("Download complete:"+baseinput+str(id)+".mp4", extra={'id': id})
    except Exception as e:
        logging.error(f"Error downloading mp4: {e}", extra={'id': id})
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
        logger.info(f'Saved MP3 to {out_mp3}')
    except ffmpeg.Error as e:
        err = e.stderr.decode() if getattr(e, 'stderr', None) else str(e)
        logger.error(f"Failed converting to MP3: {err}")
        raise



def transcribePipelineVideoByID(id):
    # lazyload whisper here to avoid the annoying waiting time
    from whisper import transcribeVideoByID

    url = fetchLecture(str(id))
    if url == "":
        logging.error("No mp4 URL found, cannot transcribe", extra={'id': id})
        return -1
    else:
        try:
            logging.info(f"Trying to directly convert to mp3 from URL: {url}", extra={'id': id})
            convert_to_mp3(url, baseinput+str(id)+".mp3")
        except Exception as e:
            logging.info("Trying to download mp4 and convert locally", extra={'id': id})
            try:
                downloadMP4(url, id)
                convert_to_mp3(baseinput+str(id)+".mp4", baseinput+str(id)+".mp3")
            except Exception as e2:
                logger.error(f"Could not convert video to mp3, aborting transcribtion for this lecture.", extra={'id': id})
                return -1

        try:
            language = transcribeVideoByID(str(id))
        except FileNotFoundError as e:
            logger.error(f"ERROR: Could not transcribe video {e}.", extra={'id': id})
            return -1
        
        try:
            save_vtt_as_blob(id,language,True)
        except Exception as e:
            logger.error(f"Could not save VTT to database {e}.", extra={'id': id})
            return -1

        logger.info(f"ID: {id} Transcription and saving completed successfully, removing source files.")
        remove_all_id_files(id)
        return 0


def fetchLecture(id) -> str:
    try: 
        response = fetchBody(id)
    except HTTPError as e:
        logger.error("Error fetching body:", extra={'id': id})
        return ""

    url = fetchMP4(id, response)
    if get_language_of_lecture(id) is None:
        logger.debug("No entry found for this lectures language in the databse, fetching lecture data ", extra={'id': id})
        getLecturerData(id, response, url)
    else:
        logger.debug("Lecturer data already exists for ID ", extra={'id': id})
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
    
    try: 
        response = fetchBody(id)
    except HTTPError as e:
        logger.error("Error fetching body:", extra={'id': id})
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    lecture_info_div = soup.find("img", class_="box nopad lecture-img").parent

    if lecture_info_div:
        
        lecturer_name = lecture_info_div.get_text()
        lecture_name= lecture_info_div.find("h3").get_text()
        h5 = lecture_info_div.find("h5")
        if h5:
            a = h5.find("a", href=True)
            if a:
                series_name = a.get_text(strip=True)
                m = re.search(r"/series/(\d+)", a["href"])
                series_id = m.group(1) if m else None

        lect_a = lecture_info_div.find("a", href=re.compile(r"^/lecturer/"))

        lectures = lecture_info_div.find_all("a", href=re.compile(r"^/lecturer/"))
        lecturer_names = []
        lecturer_ids = []
        for lect in lectures:
            lecturer_names.append(lect.get_text(strip=True))
            m = re.search(r"/lecturer/(\d+)", lect["href"])
            lecturer_ids.append(m.group(1) if m else None)
        print("lecturer_names:", lecturer_names)
        print("lecturer_ids:", lecturer_ids)
        print("lectures:", lectures)
        
        inner = lecture_info_div.decode_contents()

        def find_field(label):
            # match 'Label: ... <br' and capture the ... part
            m = re.search(rf"{re.escape(label)}:\s*(.*?)\s*<br", inner, re.I | re.S)
            return m.group(1).strip() if m else None
        
        date = find_field("Date")
        language = find_field("Language")
        duration = find_field("Duration")

        lecture_data = {
            "lecture_id": id,
            "lecturer_ids": lecturer_ids,
            "lecturer_names": lecturer_names,
            "date": date,
            "language": language,
            "duration": duration,
            "lecture_title": lecture_name,
            "series_id": series_id,
            "series_name": series_name,
            "url": url
        }
        logger.debug(f"Fetched lecture data: {lecture_data}", extra={'id': id})
        add_lecture_data(lecture_data)

        return 
    else:
        logger.error("Div not found to scrape lecture data.", extra={'id': id})
        return 
    

def remove_all_id_files(id):
    vtt_path = os.path.join(baseoutput, str(id) + ".vtt")
    txt_path = os.path.join(baseoutput, str(id) + ".txt")
    mp3_path = os.path.join(baseinput, str(id) + ".mp3")
    mp4_path = os.path.join(baseinput, str(id) + ".mp4")
    
    for file_path in [vtt_path, txt_path, mp3_path, mp4_path]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing file {file_path}: {e}")
        else:
            logger.debug(f"File not found, cannot remove: {file_path}")

if __name__ == '__main__':
    url = transcribePipelineVideoByID(str(11682))
    #transcribePipelineVideoByID(str(testid))
    #transcribePipelineVideoByID(str(11519))
    #getLecturerData(str(11516))
    #logger.info("Kratzer module loaded.", extra={'id': 123})
