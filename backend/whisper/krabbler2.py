import requests
from bs4 import BeautifulSoup
import json

url = "https://www.tele-task.de/lecture/video/11420/"
response = requests.get(url)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
player = soup.find(id="player")

if player and player.has_attr("configuration"):
    config_json = player["configuration"]
    try:
        config = json.loads(config_json)
        streams = config.get("streams")
        if streams is not None:
            sd_urls = [stream.get("sd") for stream in streams if "sd" in stream]
            print("SD URLs:")
            for url in sd_urls:
                if url.endswith("video.mp4"):
                    print(url)
                
        else:
            print("'streams' key not found in configuration.")
    except json.JSONDecodeError:
        print("Configuration attribute is not valid JSON:")
        print(config_json)
else:
    print("Element with id 'player' and attribute 'configuration' not found.")