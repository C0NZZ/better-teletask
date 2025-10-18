import whisperx
import os
from whisperx.utils import get_writer

# Get path relative to this script file, not execution location
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "output_stream.mp3")
compute_type = "int8"
device="cpu"

model = whisperx.load_model("small", device=device, compute_type=compute_type)
audio = whisperx.load_audio(file_path)

result = model.transcribe(audio)
print(result["segments"])

# Save the language before alignment
language = result["language"]

model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, device=device, return_char_alignments=False)

print(aligned_result["segments"])

# Add language back to aligned result for the writer
aligned_result["language"] = language


output_dir = os.path.join(script_dir)
os.makedirs(output_dir, exist_ok=True)

# Save as a VTT file (use aligned_result instead of result["segments"])
vtt_writer = get_writer("vtt", output_dir)
vtt_writer(
    aligned_result,
    file_path,
    {"max_line_width": None, "max_line_count": None, "highlight_words": False},
)