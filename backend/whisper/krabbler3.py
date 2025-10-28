import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
import ffmpeg
import os
from logger import log
from dotenv import load_dotenv, find_dotenv

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

testid = 11446

def fetchMP4(id):

    cookies = {"username": USERNAME_COOKIE}
    url = baseurl + id
    print("requesting "+url)
    response = requests.get(url, cookies=cookies)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    player = soup.find(id="player")

    if player and player.has_attr("configuration"):
        config_json = player["configuration"]
        try:
            # TODO ADD LOGGING
            config = json.loads(config_json)
            streams = config.get("streams")
            if streams is not None:
                print (streams)
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


if __name__ == '__main__':
    mp4_url = fetchMP4(str(testid))
    #print(mp4_url)