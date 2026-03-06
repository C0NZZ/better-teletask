import webvtt
import numpy as np
from sentence_transformers import SentenceTransformer
from database import get_vtt_file_by_id, bulk_insert_vtt_lines, get_series_of_vtt_file
from models import VttFile, VttLine

import logger
import logging
logger = logging.getLogger("btt_root_logger")

embedding_model = SentenceTransformer("BAAI/bge-m3")

# HH:MM:SS.mmm
def timestamp_to_ms(timestamp: str) -> int:
    parts = timestamp.split(':')
    if len(parts) == 3:
        h, m, rest = parts
    else:
        h = 0
        m = parts[0]
        rest = parts[1]
    s, ms = rest.split('.')
    total_ms = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)
    return total_ms

def save_vtt_lines(vtt_id: int):
    vtt_file: VttFile = get_vtt_file_by_id(vtt_id)
    series = get_series_of_vtt_file(vtt_id)
    lecturer_ids = series.lecturer_ids if series else []

    if not vtt_file:
        logger.error(f"VTT file with ID {vtt_id} not found.")
        return

    captions = list(webvtt.from_string(vtt_file.vtt_data.decode('utf-8')))
    texts = [caption.text for caption in captions]

    # Build context windows: each line gets surrounding lines for better embeddings
    WINDOW_SIZE = 2  # number of lines before and after
    context_texts = []
    for i in range(len(texts)):
        start = max(0, i - WINDOW_SIZE)
        end = min(len(texts), i + WINDOW_SIZE + 1)
        window = " ".join(texts[start:end])
        context_texts.append(window)

    # Embed the context windows, not individual lines
    logger.info(f"Computing embeddings for {len(context_texts)} lines with context window (vtt_id={vtt_id})...")
    embeddings = embedding_model.encode(context_texts, batch_size=256, show_progress_bar=False)

    vtt_lines: list[VttLine] = []
    for i, caption in enumerate(captions):
        line = VttLine(
            id=None,
            vtt_file_id=vtt_file.id,
            series_id=series.series_id,
            language=vtt_file.language,
            lecturer_ids=lecturer_ids,
            line_number=i + 1,
            ts_start=timestamp_to_ms(caption.start),
            ts_end=timestamp_to_ms(caption.end),
            content=caption.text,
            embedding=embeddings[i].tolist()
        )
        vtt_lines.append(line)    

    bulk_insert_vtt_lines(vtt_lines)



if __name__ == "__main__":

    save_vtt_lines(1)
    save_vtt_lines(2)
