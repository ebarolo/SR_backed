import os
import json
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='static/backend.log'
)

logger = logging.getLogger(__name__)

def merge_json_files(directory):
    merged_data = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    try:
                     data = json.load(json_file)
                     merged_data.append(data)
                    except json.JSONDecodeError as e:
                     logger.error(f"Errore nella decodifica del file {file_path}: {e}")
    
    logger.info(f"elenco ricette str{merged_data}")
    return merged_data

def save_merged_json(output_file, data):
    with open(output_file, 'w', encoding='utf-8') as outfile:
     json.dump(data, outfile, ensure_ascii=False, indent=4)    
