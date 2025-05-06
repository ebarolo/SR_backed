# Importazione delle librerie necessarie
import os
import base64
import asyncio
import re
import json

from tenacity import retry, stop_after_attempt, wait_exponential

from models import RecipeAIResponse

from utility import get_error_context, timeout, logger
from config import openAIclient

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

def read_prompt_files(
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
        tuple: (user_prompt, system_prompt) contenenti i testi processati
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
        print(f"Errore: File non trovato - {str(e)}")
        return None, None
    except Exception as e:
        print(f"Errore durante la lettura dei file: {str(e)}")
        return None, None

def encode_image(image_path):
    """
    Codifica l'immagine in base64.
    """
    try:

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Errore durante la codifica dell'immagine {image_path}: {str(e)}")
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

        result = await asyncio.to_thread(openAIclient.chat.completions.create(params))

        logger.info(result.choices[0])
        return result.choices[0].message.content
    except Exception as e:
        logger.error(f"Errore durante l'analisi dei fotogrammi: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(180)  # 3 minuti
async def extract_recipe_info(
    recipe_audio_text: str, recipe_caption_text: str, ingredients: any, actions: any
) -> RecipeAIResponse:

    user_prompt, system_prompt = read_prompt_files(
        recipe_audio_text,
        recipe_caption_text,
        ingredients,
        actions,
        "prompt_user_TXT.txt",
    )
    logger.info(f"readed prompts")
    
    try:
        logger.info(f"try OpenAIclient")
        OpenAIresponse = openAIclient.responses.create(
            model="o4-mini",
            input=[
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "recipe_schema",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The title of the recipe.",
                            },
                            "category": {
                                "type": "array",
                                "description": "The categories the recipe belongs to.",
                                "items": {"type": "string"},
                            },
                            "preparation_time": {
                                "type": "number",
                                "description": "The preparation time in minutes.",
                            },
                            "cooking_time": {
                                "type": "number",
                                "description": "The cooking time in minutes.",
                            },
                            "ingredients": {
                                "type": "array",
                                "description": "The list of ingredients required for the recipe.",
                                "items": {"$ref": "#/$defs/ingredient"},
                            },
                            "recipe_step": {
                                "type": "array",
                                "description": "Step-by-step instructions for preparing the recipe.",
                                "items": {"type": "string"},
                            },
                            "description": {
                                "type": "string",
                                "description": "A short description of the recipe.",
                            },
                            "diet": {
                                "type": "string",
                                "description": "Diet type associated with the recipe.",
                            },
                            "technique": {
                                "type": "string",
                                "description": "Cooking technique used in the recipe.",
                            },
                            "language": {
                                "type": "string",
                                "description": "The language of the recipe.",
                            },
                            "chef_advise": {
                                "type": "string",
                                "description": "Advice or tips from the chef.",
                            },
                            "tags": {
                                "type": "array",
                                "description": "Tags related to the recipe.",
                                "items": {"type": "string"},
                            },
                            "nutritional_info": {
                                "type": "array",
                                "description": "Nutritional information pertaining to the recipe.",
                                "items": {"type": "string"},
                            },
                            "cuisine_type": {
                                "type": "string",
                                "description": "Type of cuisine the recipe represents.",
                            },
                        },
                        "required": [
                            "title",
                            "category",
                            "preparation_time",
                            "cooking_time",
                            "ingredients",
                            "recipe_step",
                            "description",
                            "diet",
                            "technique",
                            "language",
                            "chef_advise",
                            "tags",
                            "nutritional_info",
                            "cuisine_type",
                        ],
                        "additionalProperties": False,
                        "$defs": {
                            "ingredient": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the ingredient.",
                                    },
                                    "qt": {
                                        "type": "number",
                                        "description": "The quantity of the ingredient.",
                                    },
                                    "um": {
                                        "type": "string",
                                        "description": "The unit of measurement for the ingredient.",
                                    },
                                },
                                "required": ["name", "qt", "um"],
                                "additionalProperties": False,
                            }
                        },
                    },
                }
            },
            store=False,
        )
        logger.info(f" OpenAIresponse: {OpenAIresponse}")
        if OpenAIresponse.error is None:
         # Parse the response into a RecipeSchema object
          message_items = [item for item in OpenAIresponse.output if hasattr(item, "content")]
          if not message_items:
            raise ValueError("No valid output message in OpenAIresponse")
          response_content = message_items[0].content[0]
          if isinstance(response_content, str):
            recipe_data = json.loads(response_content)
          elif hasattr(response_content, "text"):
            recipe_data = json.loads(response_content.text)
          else:
            recipe_data = response_content

          return RecipeAIResponse(**recipe_data)
        else:
            raise ValueError("OpenAIresponse error: " + OpenAIresponse.error)

    except Exception as e:
        logger.error(f"OpenAIresponse error: {str(e)}")
        raise e


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(300)  # 5 minuti di timeout
async def whisper_speech_recognition(audio_file_path: str, language: str) -> str:
    try:
        with open(audio_file_path, "rb") as audio_file:
            # Usiamo asyncio.to_thread per eseguire la chiamata bloccante in un thread separato
            # Controlla la dimensione del file audio in KB
            audio_file.seek(0, 2)  # spostati alla fine del file
            file_size_bytes = audio_file.tell()
            audio_file.seek(0)     # torna all'inizio del file
            file_size_kb = file_size_bytes / 1024
            logger.info(f"Dimensione file audio: {file_size_kb:.2f} KB")
            transcription = await asyncio.to_thread(
                openAIclient.audio.transcriptions.create,
                model="gpt-4o-transcribe",
                file=audio_file,
            )
            logger.info(f"transcription: {transcription}")
        return transcription.text
    except FileNotFoundError:
        error_context = get_error_context()
        logger.error(
            f"Errore: Il file audio '{audio_file_path}' non è stato trovato. - {error_context}"
        )
        raise e
    except Exception as e:
        error_context = get_error_context()
        logger.error(
            f"Errore durante il riconoscimento vocale: {str(e)} - {error_context}"
        )
        raise e
