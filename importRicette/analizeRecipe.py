# Importazione delle librerie necessarie
import os
import base64
import logging
import asyncio
import re
import json

from tenacity import retry, stop_after_attempt, wait_exponential
from config import OpenAIclient

from models import RecipeAIResponse, recipe_schema

from utility import get_error_context, timeout

logger = logging.getLogger(__name__)

# Funzione per convertire il testo in un dizionario
def testo_a_dizionario(testo):
    risultato = {}
    linee = testo.strip().split("\n")
    chiave_corrente = None
    valore_corrente = []
    for linea in linee:
        if not linea.strip():
            continue
        # Verifica se la linea è una chiave
        if re.match(r"^\w+:", linea):
            if chiave_corrente:
                risultato[chiave_corrente] = "\n".join(valore_corrente).strip()
            chiave_corrente, resto = linea.split(":", 1)
            chiave_corrente = chiave_corrente.strip()
            valore_corrente = [resto.strip()]
        else:
            valore_corrente.append(linea.strip())
    if chiave_corrente:
        risultato[chiave_corrente] = "\n".join(valore_corrente).strip()
    return risultato

def create_prompt(
    recipe_audio_text="",
    recipe_capiton_text="",
    ingredients=None,
    actions=None,
    file_name="",
):
    """
    Legge i file di prompt e sostituisce le variabili con i valori forniti.

    Args:
        recipe_text (str): Il testo della ricetta da sostituire
        ingredients (list): Lista degli ingredienti
        actions (list): Lista delle azioni

    Returns:
        tuple: (user_prompt, system_prompt) contenenti i prompt processati
    """
    # Inizializza liste vuote se non fornite
    if ingredients is None:
        ingredients = []
    if actions is None:
        actions = []

    try:
        # Leggi i file dalla cartella static
        base_path = os.path.join("static")

        # Leggi prompt_user.txt
        with open(os.path.join(base_path, file_name), "r", encoding="utf-8") as file:
            user_prompt = file.read()

        # Leggi prompt_system.txt
        with open(
            os.path.join(base_path, "prompt_system.txt"), "r", encoding="utf-8"
        ) as file:
            system_prompt = file.read()

        # Converti gli array in stringhe
        ingredients_text = "\n".join(ingredients) if ingredients else ""
        actions_text = "\n".join(actions) if actions else ""

        # Sostituisci le variabili nel testo
        variables = {
            "{recipe_audio}": recipe_audio_text,
            "{recipe_caption}": recipe_capiton_text,
            "{ingredients}": ingredients_text,
            "{actions}": actions_text,
        }

        # Effettua le sostituzioni in entrambi i prompt
        for var, value in variables.items():
            user_prompt = user_prompt.replace(var, value)
            system_prompt = system_prompt.replace(var, value)

        return user_prompt, system_prompt

    except FileNotFoundError as e:
        error_context = get_error_context()
        logger.error(f"Errore: File non trovato - {e} - {error_context}")
        return None, None
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore durante la lettura dei file: {e} - {error_context}")
        return None, None

def encode_image(image_path):
    """
    Codifica l'immagine in base64.
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore durante la codifica dell'immagine {image_path}: {e} - {error_context}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(300)
async def analyze_recipe_frames(base64Frames):
    try:
        PROMPT_MESSAGES = [
            {
                "role": "system",
                "content": "You are an assistant expert in culinary image analysis. Your task is to identify ingredients and cooking actions from an image.",
            },
            {
                "role": "user",
                "content": [
                    "These are frames from a video recipe that I want to upload. Identify the visible ingredients and the actions that are executed. Provide the answer in JSON format with three keys: 'ingredients' , 'actions', description.",
                    *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::50]),
                ],
            },
        ]
        # logger.info({PROMPT_MESSAGES})
        params = {
            "model": "gpt-4o-mini",
            "messages": PROMPT_MESSAGES,
            "max_tokens": 700,
        }

        result = await asyncio.to_thread(OpenAIclient.chat.completions.create(params))

        logger.info(result.choices[0])
        return result.choices[0].message.content
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore durante l'analisi dei fotogrammi: {e} - {error_context}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(60)  # 3 minuti
async def extract_recipe_info(
    recipe_audio_text: str, recipe_caption_text: str, ingredients: any, actions: any
) -> RecipeAIResponse:

    user_prompt, system_prompt = create_prompt(
        recipe_audio_text,
        recipe_caption_text,
        ingredients,
        actions,
        "prompt_user_TXT.txt",
    )
    logger.info(f"created prompts")
    
    try:
        logger.info(f"try call OpenAI")
        OpenAIresponse = await asyncio.to_thread(
            OpenAIclient.responses.create,
            model="o4-mini",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            text=recipe_schema,
            reasoning={"effort": "low"},
            tools=[],
            store=True,
            timeout=60
        )
        logger.info(f" OpenAIresponse: {OpenAIresponse}")
        
        if OpenAIresponse.error is None:
         # Parse the response into a RecipeSchema object
          message_items = [item for item in OpenAIresponse.output if hasattr(item, "content")]
          if not message_items:
            logger.error(f"No valid output message in OpenAIresponse {OpenAIresponse}")
            raise ValueError(f"No valid output message in OpenAIresponse {OpenAIresponse}")
          response_content = message_items[0].content[0]
          if isinstance(response_content, str):
            recipe_data = json.loads(response_content)
          elif hasattr(response_content, "text"):
            recipe_data = json.loads(response_content.text)
          else:
            recipe_data = response_content
          
          logger.info(f"RecipeAIResponse: {recipe_data}")
          return RecipeAIResponse(**recipe_data)
        else:
            raise ValueError("OpenAIresponse error: " + OpenAIresponse.error)

    except Exception as e:
        error_context = get_error_context()
        logger.error(f"OpenAIresponse error: {e} - {error_context}")
        raise e


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(300)  # 5 minuti di timeout
async def whisper_speech_recognition(audio_file_path: str, language: str) -> str:
    try:
        with open(audio_file_path, "rb") as audio_file:
            # Usiamo asyncio.to_thread per eseguire la chiamata bloccante in un thread separato
            transcription = await asyncio.to_thread(
                OpenAIclient.audio.transcriptions.create,
                model="gpt-4o-mini-transcribe",
                file=audio_file,
            )
        return transcription.text
    except FileNotFoundError as e:
        error_context = get_error_context()
        logger.error(f"Errore: Il file audio '{audio_file_path}' non è stato trovato. - {e} - {error_context}")
        raise e
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore durante il riconoscimento vocale: {e} - {error_context}")
        raise e
