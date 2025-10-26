import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
import ffmpeg
import os
from logger import log

script_dir = os.path.dirname(os.path.abspath(__file__))
baseoutput =  os.path.join(script_dir, "input/")
baseurl = "https://www.tele-task.de/lecture/video/" 
url = "https://www.tele-task.de/lecture/video/11420/"

def fetchMP4(id):
    url = baseurl+id
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
                        return url
                    
            else:
                print("'streams' key not found in configuration.")
        except json.JSONDecodeError:
            print("Configuration attribute is not valid JSON:")
            print(config_json)
    else:
        print("Element with id 'player' and attribute 'configuration' not found.")


def downloadMP4(url):
    print(f"Downloading: {url}")
    try:
        mp4_response = requests.get(url, stream=True)
        mp4_response.raise_for_status()
        total_size = int(mp4_response.headers.get('content-length', 0))
        with open(baseoutput+id+".mp4", "wb") as f, tqdm(
            desc="Downloading "+baseoutput+id+".mp4",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in mp4_response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
        print("Download complete:"+baseoutput+id+".mp4")
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


def fetch_and_convert(id):
    # Find MP4 URL
    mp4url = fetchMP4(id)
    if not mp4url:
        print('No MP4 URL found')
        log(f"❌ ID: {id} ERROR: No MP4 URL found for teletask video.")
        return -1

    # Try direct conversion from remote URL
    try:
        print('Attempting direct conversion from URL to MP3...')
        print(baseoutput+id+".mp3")
        convert_to_mp3(mp4url, baseoutput+id+".mp3")
        print('Created '+baseoutput+id+".mp3")
        log(f"✅ ID: {id} Direct conversion from URL to MP3 succeeded.")
    except Exception:
        log(f"❌ ID: {id} Direct conversion failed, downloading then converting.")
        print('Direct conversion failed, downloading then converting...')
        try:
            downloadMP4(mp4url)
            convert_to_mp3(baseoutput+id+".mp4", baseoutput+id+".mp3")
            print('Created'+baseoutput+id+".mp3")
        except Exception:
            log(f"❌ ID: {id} ERROR ABORTING converting downloaded MP4 to MP3:")
            print('ERROR converting downloaded MP4 to MP3:')
            return -1


if __name__ == '__main__':

    id="1"
    fetch_and_convert(id)

#mp4url = fetchMP4(url)
#downloadMP4(mp4url)