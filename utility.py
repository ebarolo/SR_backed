import re
import os
import datetime
import logging
import random

BASE_FOLDER = os.path.join(os.getcwd(), "static/ricette")

# Sanificazione iniziale del testo
def sanitize_text(text):
    # Rimuove emoji, simboli non ASCII e hashtag
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'#\w+', '', text)  # Rimuove hashtag
    text = re.sub(r'@[\w]+', '', text)  # Rimuove menzioni
    text = text.strip()
    return text

def sanitize_filename(filename: str) -> str:
    return "".join(c for c in filename if c.isalnum() or c.isspace()).strip()

def sanitize_folder_name(folder_name: str) -> str:
    # Sostituisce i caratteri non validi con un carattere di sottolineatura
    return re.sub(r'[<>:"/\\|?*]', '_', folder_name)

def is_number(value):
    """Verifica se il valore è un numero."""
    try:
        float(str(value))
        return True
    except (ValueError, TypeError):
        return False
    
def create_date_folder() -> str:
    """Crea una cartella con la data odierna se non esiste già."""
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder = os.path.join(BASE_FOLDER, today)
    os.makedirs(date_folder, exist_ok=True)
    return date_folder

def rename_files(video_folder,file_name:str):
     # Rinominare tutti i file nella cartella video_folder_new mantenendo l'estensione originale
    for filename in os.listdir(video_folder):
        old_file_path = os.path.join(video_folder, filename)
        name, ext = os.path.splitext(filename)  # Separare nome ed estensione
        new_file_path = os.path.join(video_folder, f"{file_name}{ext}")
        os.rename(old_file_path, new_file_path)
    return ""

def rename_folder(percorso_vecchio: str, nuovo_nome: str) -> bool:
    """
    Rinomina una cartella in modo sicuro.
    
    Args:
        percorso_vecchio: Percorso completo della cartella da rinominare
        nuovo_nome: Nuovo nome della cartella
        
    Returns:
        bool: True se il rinominamento è avvenuto con successo, False altrimenti
    """
    try:
        if not os.path.exists(percorso_vecchio):
            logging.error(f"La cartella {percorso_vecchio} non esiste")
            return percorso_vecchio
            
        cartella_base = os.path.dirname(percorso_vecchio)
        percorso_nuovo = os.path.join(cartella_base, nuovo_nome)
        
        if os.path.exists(percorso_nuovo):
         logging.error(f"Esiste già una cartella chiamata {nuovo_nome}")
         percorso_nuovo = percorso_nuovo+"_"+str(random.randint(0,100)) 
        os.rename(percorso_vecchio, percorso_nuovo)
        logging.info(f"Cartella rinominata da {percorso_vecchio} a {percorso_nuovo}")
        return percorso_nuovo
        
    except OSError as e:
        logging.error(f"Errore durante il rinominamento della cartella: {str(e)}")
        return percorso_vecchio
