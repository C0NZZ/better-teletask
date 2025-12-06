import whisperx
import os
from whisperx.utils import get_writer
from dotenv import load_dotenv, find_dotenv
from logger import log
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
    try:
        # fail early if input audio doesn't exist
        if not os.path.exists(file_path):
            msg = f"❌ ID: {id} ERROR: input audio file not found: {file_path}"
            log(msg)
            print(msg)
            return ""
        

        language = None
        try:
            language = get_language_of_lecture(int(id))
            print(f"Fetched language from database: {language}")
        except Exception as e:
            print(f"Could not fetch language from database, defaulting to whisperx auto-detection. Error: {e}")

        audio = whisperx.load_audio(file_path)

        result = model.transcribe(audio, batch_size=4, language=language)
        print(result["segments"])

        # Save the language before alignment
        language = result.get("language")

        print("language is " + str(language))

        model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
        aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, device=device, return_char_alignments=False)

        # print(aligned_result["segments"])

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
    except Exception as e:
        # log and return -1 to signal failure
        log(f"❌ ID: {id} ERROR: {e}")
        print(f"❌ ID: {id} ERROR: {e}")
        raise


if __name__ == '__main__':
    id="11517"
    transcribeVideoByID(id)