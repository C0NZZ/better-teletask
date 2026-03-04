import requests
import os
from dotenv import load_dotenv
import re
from typing import List, Dict, Any, Optional, Tuple
from database import get_original_vtt_by_id, get_original_language_by_id

import logger
import logging
logger = logging.getLogger("btt_root_logger")

load_dotenv()

ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
model_name = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

# if script ran is located in other folder
script_dir = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(script_dir, os.getenv("VTT_DEST_FOLDER", "output/"))


LANGUAGES: Dict[str, str] = {
    "de": "German",
    "en": "English",
}


# regex: HH:MM:SS.mmm --> HH:MM:SS.mmm [optional settings]
TIMESTAMP_LINE_PATTERN = re.compile(
    r"(\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}\.\d{3}(?:[^\n]*))"
)


def get_original_translation(config: Dict[str, Any]) -> str:

    try:
        return read_file_content(config['input_file'])
    except FileNotFoundError as e:
        logger.debug(f"Input file not found: {e}. Attempting to retrieve from database.", extra={'id': config['id']})

    try:
        return get_original_vtt_by_id(int(config['id']))
    except Exception as db_e:
        logger.debug(f"Failed to retrieve original translation from database: {db_e}", extra={'id': config['id']})

    return None;
            

def generate_config(id: int, from_language: str, to_language: str, ollama_url: str, model_name: str) -> Dict[str, Any]:
    return {
        "id": id,
        "input_file": f"{output_folder}{id}.vtt",
        "output_file": f"{output_folder}{id}{to_language}.vtt",
        "ollama_url": ollama_url,
        "model_name": model_name,
        "chunk_size_chars": 3500,
        "context_window_chars": 500,
        "from_language": from_language,
        "to_language": to_language,
    }

def read_file_content(file_path: str) -> str:
    """Reads the entire content of a text file."""  
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file '{file_path}' not found.")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def parse_vtt_blocks(raw_content: str) -> Tuple[str, List[str]]:
    """
    Splits raw VTT content into blocks and separates the header.
    """
    normalized_content: str = raw_content.replace("\r\n", "\n")
    blocks: List[str] = normalized_content.split("\n\n")
    
    if blocks and "WEBVTT" in blocks[0].upper():
        header: str = blocks[0].strip()
        actual_blocks: List[str] = blocks[1:]
    else:
        header = "WEBVTT"
        actual_blocks = blocks

    cleaned_blocks: List[str] = [b.strip() for b in actual_blocks if b.strip()]

    return header, cleaned_blocks

def process_block_timestamps(blocks: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """
    Extracts timestamps from each block and maps them to a placeholder.
    Returns: (List of cleaned dialogue blocks, Map of placeholder -> timestamp)
    """
    clean_blocks: List[str] = []
    timestamp_map: Dict[str, str] = {}
    
    for i, block in enumerate(blocks):
        # Find the timestamp line using the compiled regex
        match = TIMESTAMP_LINE_PATTERN.search(block)
        
        if match:
            timestamp_line: str = match.group(1).strip()
            
            # The placeholder is unique for each block's index
            placeholder: str = f"TS{i}"
            timestamp_map[placeholder] = timestamp_line
            
            # Remove the timestamp line and any subsequent newlines/whitespace
            # We replace the entire match with the placeholder
            cleaned_content: str = TIMESTAMP_LINE_PATTERN.sub(placeholder, block, 1).strip()
            
            # Remove any trailing line numbers or whitespace
            lines = cleaned_content.split('\n')
            
            # Assume the first line of the block *after* timestamp removal might be a line number (like '1', '2', etc.)
            # A simple way to clean is just to take all lines after the first one and join them.
            if len(lines) > 1 and lines[0].strip().isdigit():
                cleaned_content = '\n'.join(lines[1:])
            
            clean_blocks.append(cleaned_content.strip())
        else:
            # If a block has no timestamp (e.g., just comments/notes), pass it through
            clean_blocks.append(block)

    return clean_blocks, timestamp_map

def group_blocks_into_chunks(blocks: List[str], max_chars: int) -> List[str]:
    """Groups subtitle blocks into chunks."""
    chunks: List[str] = []
    current_batch: List[str] = []
    current_length: int = 0

    for block in blocks:
        block_len: int = len(block)
        
        if current_length + block_len > max_chars and current_batch:
            chunks.append("\n\n".join(current_batch))
            current_batch = []
            current_length = 0
        
        current_batch.append(block)
        current_length += block_len

    if current_batch:
        chunks.append("\n\n".join(current_batch))
        
    return chunks

def build_translation_prompt(chunk_text: str, from_language: str, to_langauge:str, previous_context: str = "") -> str:
    """
    Constructs the prompt string. The chunk_text now contains TSx placeholders.
    """
    context_section: str = ""
    if previous_context:
        # Note: The context buffer might contain TSx from the previous run,
        # which is okay as it helps the model track where dialogue segments begin/end.
        context_section = (
            "### CONTEXT (Preceding translated text - FOR REFERENCE ONLY, DO NOT TRANSLATE)\n"
            f"{previous_context}\n"
            "### END CONTEXT\n\n"
        )

    return f"""You are a precise subtitle translator. 
{context_section}
Translate the following VTT subtitle dialogue block from {from_language} to {to_langauge}.

Requirements:
- Preserve ALL placeholder tokens EXACTLY (e.g., TS1, TS2).
- Preserve line breaks and block structure.
- Preserve technical words, names, and any non-translatable terms as they are.
- Translate ONLY the spoken text lines.
- Do not add or remove content.
- Use the provided CONTEXT (if any) to ensure consistency.
- Only change content, when language specific proverbs or idioms are used. In that case, try to find an equivalent in the target language, but keep the meaning as close as possible.

### INPUT BLOCK TO TRANSLATE (Dialogue Only):

{chunk_text}"""

def query_ollama(prompt: str, url: str, model: str) -> Optional[str]:
    """Sends the prompt to Ollama and returns the response text."""
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        logger.error(f"  [!] Request failed: {e}")
        return None

PLACEHOLDER_PATTERN = re.compile(r'TS\d+')


def reinsert_timestamps(translated_blocks: List[str], timestamp_map: Dict[str, str]) -> List[str]:
    """Replaces placeholder tokens with original timestamps."""
    
    def replace_placeholder(match: re.Match) -> str:
        placeholder = match.group(0)
        return timestamp_map.get(placeholder, placeholder)
    
    return [PLACEHOLDER_PATTERN.sub(replace_placeholder, block) for block in translated_blocks]

def save_vtt_file(file_path: str, header: str, content_blocks: List[str]) -> None:
    """Assembles blocks, prepends the header, and writes the final VTT file."""
    
    translated_content: str = "\n\n".join(content_blocks)
    final_output: str = f"{header}\n\n{translated_content}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_output)

def run_translation_workflow(id: int, to_langauge: str, from_language: Optional[str]) -> None:
    """Orchestrates the translation with full pre- and post-processing."""
    
    logger.info(f"--- Starting translation for {id} to {to_langauge} ---")

    if from_language is None:
        from_language = get_original_language_by_id(id)

    config: Dict[str, Any] = generate_config(id, from_language, to_langauge, ollama_url, model_name)
    logger.debug(f"Configuration: {config}")
    
    raw_content: str = get_original_translation(config)

    if raw_content is None:
        logger.error(f"No valid translation source found for ID {id}. Aborting translation.", extra={'id': id})
        return
    
    header, blocks = parse_vtt_blocks(raw_content)


    dialogue_blocks, timestamp_map = process_block_timestamps(blocks)
    
  
    chunks: List[str] = group_blocks_into_chunks(dialogue_blocks, config['chunk_size_chars'])
    
    total_chunks: int = len(chunks)
    translated_chunks_with_placeholders: List[str] = []
    context_buffer: str = ""

    logger.debug(f"Identified {len(blocks)} subtitle blocks. Created {total_chunks} token-efficient chunks.")
    logger.debug(f"Header '{header}' will be preserved.")

  
    
    for i, chunk in enumerate(chunks):
        logger.debug(f"Translating chunk {i + 1}/{total_chunks}...")
        
        prompt: str = build_translation_prompt(chunk, LANGUAGES[config['from_language']], LANGUAGES[config['to_language']], context_buffer)
        result: Optional[str] = query_ollama(prompt, config['ollama_url'], config['model_name'])
        
        if result:
            translated_chunks_with_placeholders.append(result)
            window_size: int = config['context_window_chars']
            # Context buffer still uses the result (which contains the clean dialogue and placeholders)
            context_buffer = result[-window_size:] 
        else:
            logger.error(f"  [!] chunk {i + 1} failed. Appending original dialogue.")
            translated_chunks_with_placeholders.append(chunk)

    
    translated_blocks_flat: List[str] = "\n\n".join(translated_chunks_with_placeholders).split('\n\n')
    
    final_translated_blocks: List[str] = reinsert_timestamps(translated_blocks_flat, timestamp_map)

    save_vtt_file(config['output_file'], header, final_translated_blocks)
    logger.info(f"--- Process Complete. Saved to {config['output_file']} ---")

if __name__ == "__main__":
    run_translation_workflow(11402, "en", "de")