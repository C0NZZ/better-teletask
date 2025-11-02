import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
import ffmpeg
import os
from logger import log
from dotenv import load_dotenv, find_dotenv
from database2 import getHighestTeletaskID

load_dotenv(find_dotenv())

OUTPUTFOLDER = os.environ.get("VTT_DEST_FOLDER")
INPUTFOLDER = os.environ.get("RECORDING_SOURCE_FOLDER")
USERNAME_COOKIE = os.environ.get("USERNAME_COOKIE")
print(OUTPUTFOLDER)
print(INPUTFOLDER)
print(USERNAME_COOKIE)

script_dir = os.path.dirname(os.path.abspath(__file__))
baseoutput =  os.path.join(script_dir, "input/")
baseurl = "https://www.tele-task.de/lecture/video/"

testid = 11413

def fetchMP4(id) -> str:

    cookies = {"username": USERNAME_COOKIE}
    url = baseurl + id
    print("requesting "+url)
    response = requests.get(url, cookies=cookies)
    response.raise_for_status()

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
        response = requests.get(url, cookies=cookies)
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
    highest = getHighestTeletaskID() + 1
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
    


if __name__ == '__main__':
    #pingVideoByID(str(2110))
    print(get_upper_ids())