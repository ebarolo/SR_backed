# Importazione delle librerie necessarie
import os
import base64
import asyncio
import re
import json
import requests

from tenacity import retry, stop_after_attempt, wait_exponential

from utility import get_error_context, timeout, logger

from config import (
    openAIclient,
    BASE_FOLDER_RICETTE,
    OPENAI_VISION_CHAT_MODEL,
    OPENAI_RESPONSES_MODEL,
    OPENAI_TRANSCRIBE_MODEL,
    OPENAI_IMAGE_MODEL,
)
from models import recipe_schema

def read_prompt_files(file_name: str, **kwargs) -> str:
    """
    Legge un file di prompt e sostituisce i segnaposto con i valori forniti.

    Args:
        file_name (str): Il nome del file da leggere dalla cartella 'static'.
        **kwargs: Coppie chiave-valore per le sostituzioni. 
                  Ogni `{chiave}` nel file verrà sostituita con `valore`.

    Returns:
        str: Il testo del file con le sostituzioni effettuate.
    """
    try:
        # Costruisci il percorso completo del file
        file_path = os.path.join("static", "PROMPT", file_name)

        # Leggi il contenuto del file
        with open(file_path, "r", encoding="utf-8") as file:
            prompt_text = file.read()

        # Effettua le sostituzioni
        for key, value in kwargs.items():
            # Assicura che il valore sia una stringa prima della sostituzione
            str_value = "\n".join(value) if isinstance(value, list) else str(value)
            prompt_text = prompt_text.replace(f"{{{key}}}", str_value)

        return prompt_text

    except FileNotFoundError:
        logger.error(f"File di prompt non trovato: {file_path}")
        # Rilanciare l'eccezione è spesso meglio che restituire None
        raise
    except Exception as e:
        logger.error(f"Errore durante la lettura del file di prompt {file_path}: {str(e)}")
        raise

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
            "model": OPENAI_VISION_CHAT_MODEL,
            "messages": PROMPT_MESSAGES,
            "max_tokens": 700,
        }

        # Esegui la chiamata bloccante nel thread pool passando i kwargs correttamente
        result = await asyncio.to_thread(openAIclient.chat.completions.create, **params)

        #logger.info(result.choices[0])
        return result.choices[0].message.content
    except Exception as e:
        logger.error(f"Errore durante l'analisi dei fotogrammi: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(180)  # 3 minuti
async def extract_recipe_info( recipe_audio_text: str, recipe_caption_text: str, ingredients: any, actions: any
 ):

    # Prepara i valori per i segnaposto
    replacements = {
        "recipe_audio": recipe_audio_text,
        "recipe_caption": recipe_caption_text,
        "ingredients": ingredients if ingredients else [],
        "actions": actions if actions else [],
    }

    # Leggi e popola i prompt in modo dinamico
    user_prompt = read_prompt_files("prompt_user_TXT.txt", **replacements)
    system_prompt = read_prompt_files("prompt_system.txt", **replacements)
        
    try:
        
        OpenAIresponse = await asyncio.to_thread(
            openAIclient.responses.create,
            model=OPENAI_RESPONSES_MODEL,
            input=[
             {
                "role": "developer",
                "content": [
                    {
                    "type": "input_text",
                    "text": system_prompt
                    }
                ]
             },
             {
                "role": "user",
                "content": [
                    {
                    "type": "input_text",
                    "text": user_prompt
                    }
                ]
             }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": recipe_schema.get("name", "recipe_schema"),
                    "strict": bool(recipe_schema.get("strict", True)),
                    "schema": recipe_schema.get("schema", {}),
                },
                "verbosity": "medium"
            },
            reasoning={
                "effort": "low",
                "summary": "auto"
            },
            tools=[],
            store=True
        )
        
        logger.info(f" OpenAIresponse: {OpenAIresponse}")
        if OpenAIresponse.error is None:
            # 1) Prova proprietà comoda se presente
            output_text = getattr(OpenAIresponse, "output_text", None)
            if output_text:
                try:
                    return json.loads(output_text)
                except Exception:
                    logger.warning("Failed to parse output_text as JSON")

            # 2) Estrai il primo messaggio con content non vuoto e prendi il testo
            output_items = getattr(OpenAIresponse, "output", []) or []
            # Preferisci i messaggi veri e propri
            message_items = [
                item for item in output_items
                if getattr(item, "type", "") == "message" and getattr(item, "content", None)
            ]
            # Se non trovi "message", ripiega su qualsiasi item con content non vuoto (ma evita quelli None)
            if not message_items:
                message_items = [
                    item for item in output_items
                    if getattr(item, "content", None)
                ]
            if not message_items:
                raise ValueError("Nessun contenuto valido presente in OpenAIresponse.output")

            # Scorri le parti di contenuto e trova del testo JSON
            for part in getattr(message_items[0], "content", []) or []:
                try:
                    if isinstance(part, str):
                        return json.loads(part)
                    text_value = getattr(part, "text", None)
                    if text_value:
                        return json.loads(text_value)
                except Exception:
                    continue

            raise ValueError("Impossibile estrarre JSON dal contenuto della risposta OpenAI")
        else:
            raise ValueError("OpenAIresponse error: " + str(OpenAIresponse.error))

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
            transcription = await asyncio.to_thread(
                openAIclient.audio.transcriptions.create,
                model=OPENAI_TRANSCRIBE_MODEL,
                file=audio_file,
            )
            logger.info(f"transcription: {transcription}")
        return transcription.text
    except FileNotFoundError as e:
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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(300)  # 5 minuti di timeout
async def generateRecipeImages(ricetta: dict, shortcode: str):
    # Costruisci un testo robusto per il prompt a partire dai campi di ricetta
    image_folder = os.path.join(BASE_FOLDER_RICETTE, shortcode, "media_recipe")
    title = str(ricetta.get("title", ""))
    description = str(ricetta.get("description", ""))
    ingredients = ricetta.get("ingredients", [])
    if isinstance(ingredients, list):
        ingredient_parts = []
        for ing in ingredients:
            if isinstance(ing, dict):
                name = str(ing.get("name") or "")
                qt = ing.get("qt")
                qt_str = str(qt) if qt is not None else ""
                um = str(ing.get("um") or "")
                piece = " ".join([x for x in [name, qt_str, um] if x])
                if piece:
                    ingredient_parts.append(piece)
            else:
                ingredient_parts.append(str(ing))
        ingredients_text = ", ".join(ingredient_parts)
    else:
        ingredients_text = str(ingredients)

    steps = ricetta.get("recipe_step", [])
    if isinstance(steps, list):
        steps_text = ". ".join([str(s) for s in steps])
    else:
        steps_text = str(steps)
        
    tipologiaImmagin = []
    '''
    tipologiaImmagin = [{
        "type": "copertina",
        "testo":  " ".join([p for p in [title, description] if p])
    }]
    
    tipologiaImmagin.append({
        "type": "stepricetta",
        "testo": " ".join([p for p in [title, steps_text] if p])
    })
   
    tipologiaImmagin.append({
        "type": "ingredienti",
        "testo": " ".join([p for p in [ingredients_text] if p])
    })
     '''
    all_saved_paths = []
    for img in tipologiaImmagin:
     replacements = {
      "testo": img["testo"]
     }

     # Leggi e popola i prompt in modo dinamico
     image_prompt = read_prompt_files("prompt_immagini_ricetta.txt", **replacements)

     try:
        
        OpenAIresponse = await asyncio.to_thread(
            openAIclient.images.generate,
            model=OPENAI_IMAGE_MODEL,
            prompt=image_prompt,
            size="1536x1024",
            output_format="jpeg",
            quality="high",
            n=1
        )
        
        #logger.info(f" OpenAIresponse: {OpenAIresponse}")
        # Salva le immagini nella cartella image_folder
        try:
           
            os.makedirs(image_folder, exist_ok=True)
            saved_paths = []
            data_items = []
            if hasattr(OpenAIresponse, "data"):
                data_items = getattr(OpenAIresponse, "data") or []
            elif isinstance(OpenAIresponse, dict) and "data" in OpenAIresponse:
                data_items = OpenAIresponse.get("data") or []

            if not isinstance(data_items, list) or len(data_items) == 0:
                raise ValueError("La risposta immagini non contiene alcun elemento in 'data'")

            for idx, item in enumerate(data_items[:3]):
                image_bytes = None
                b64_val = None
                url_val = None

                if hasattr(item, "b64_json"):
                    b64_val = getattr(item, "b64_json")
                elif isinstance(item, dict):
                    b64_val = item.get("b64_json")

                if not b64_val:
                    if hasattr(item, "url"):
                        url_val = getattr(item, "url")
                    elif isinstance(item, dict):
                        url_val = item.get("url")

                if b64_val:
                    image_bytes = base64.b64decode(b64_val)
                elif url_val:
                    resp = requests.get(url_val, timeout=30)
                    resp.raise_for_status()
                    image_bytes = resp.content
                else:
                    raise ValueError("Elemento immagine privo di 'b64_json' e 'url'")

                out_path = os.path.join(image_folder, f"image_{img['type']}_{idx+1}.jpg")
                with open(out_path, "wb") as f:
                    f.write(image_bytes)
                saved_paths.append(out_path)
                logger.info(f"Immagine salvata: {out_path}")

            all_saved_paths.extend(saved_paths)
        except Exception as e:
            logger.error(f"Errore durante il salvataggio delle immagini: {str(e)}")
            raise

     except Exception as e:
        logger.error(f"OpenAIresponse error: {str(e)}")
        raise e

    return all_saved_paths
