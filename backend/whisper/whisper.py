# setup logging
import logger
import logging
logger = logging.getLogger("btt_root_logger")
logger.propagate = False


import whisperx
import os
from whisperx.utils import get_writer
from dotenv import load_dotenv, find_dotenv
from database import get_language_of_lecture


load_dotenv(find_dotenv())
MODEL = os.environ.get("ASR_MODEL")
COMPUTE_TYPE = os.environ.get("COMPUTE_TYPE")

# Get path relative to this script file, not execution location
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "input/")
output_path = os.path.join(script_dir, "output/")
compute_type = COMPUTE_TYPE
device = "cuda"

model = whisperx.load_model(MODEL, device=device, compute_type=compute_type)

def transcribeVideoByID(id) -> str: 
    file_path = os.path.join(input_path, id + ".mp3")
    
    # fail early if input audio doesn't exist
    if not os.path.exists(file_path):
        logger.error(f"input audio file not found: {file_path}", extra={'id': id})
        raise FileNotFoundError(f"input audio file not found: {file_path}")
    
    language = None
    try:
        language = get_language_of_lecture(int(id))
        logger.info(f"Fetched language from database: {language}", extra={'id': id})
    except Exception as e:
        logger.warning(f"Could not fetch language from database. {e}", extra={'id': id})
        print(f"Could not fetch language from database. {e}")

    if language is None:
        logger.info(f"No language found in database, defaulting to auto detection from whisperx.", extra={'id': id})
        language = None

    print(language)
    audio = whisperx.load_audio(file_path)

    result = model.transcribe(audio, batch_size=4, language=language)
    print(result["segments"])

    # Save the language before alignment
    language = result.get("language")

    print("language is " + str(language))

    model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
    
    aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, device=device, return_char_alignments=False)

    

    # Add language back to aligned result for the writer
    aligned_result["language"] = language

    os.makedirs(output_path, exist_ok=True)

    # Save as a VTT file (use aligned_result instead of result["segments"])
    vtt_writer = get_writer("vtt", output_path)
    vtt_writer(
        aligned_result,
        file_path,
        {"max_line_width": None, "max_line_count": None, "highlight_words": False},
    )

    txt_writer = get_writer("txt", output_path)
    txt_writer(
        aligned_result,
        file_path,
        {"max_line_width": None, "max_line_count": None, "highlight_words": False},
    )

    return language
    


if __name__ == '__main__':
    id="11401"
    transcribeVideoByID(id)