# Importazione delle librerie necessarie
import os
import base64
import asyncio
import json
import requests
import openai

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type

from utility.utility import timeout
from utility.logging_config import get_error_logger
from utility.timeout_config import TimeoutConfig, TimeoutContext
from utility.openai_errors import (
    classify_openai_error,
    QuotaExceededError,
    InvalidAPIKeyError,
    OpenAIError
)

error_logger = get_error_logger(__name__)

from config import (
    openAIclient,
    BASE_FOLDER_RICETTE,
    OPENAI_VISION_CHAT_MODEL,
    OPENAI_RESPONSES_MODEL,
    OPENAI_TRANSCRIBE_MODEL,
    OPENAI_IMAGE_MODEL,
)
from utility.models import recipe_schema
from utility.path_utils import ensure_media_web_path

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
        file_path = os.path.join("static", "prompt", file_name)

        # Leggi il contenuto del file
        with open(file_path, "r", encoding="utf-8") as file:
            prompt_text = file.read()

        # Effettua le sostituzioni
        for key, value in kwargs.items():
            # Assicura che il valore sia una stringa prima della sostituzione
            str_value = "\n".join(value) if isinstance(value, list) else str(value)
            prompt_text = prompt_text.replace(f"{{{key}}}", str_value)

        return prompt_text

    except FileNotFoundError as e:
        error_logger.log_exception("prompt_file_not_found", e, {"file_path": file_path})
        # Rilanciare l'eccezione è spesso meglio che restituire None
        raise
    except Exception as e:
        error_logger.log_exception("prompt_file_read", e, {"file_path": file_path})
        raise

def encode_image(image_path):
    """
    Codifica l'immagine in base64.
    """
    try:

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        error_logger.log_exception("image_encoding", e, {"image_path": image_path})
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_not_exception_type((QuotaExceededError, InvalidAPIKeyError, OpenAIError))
)
@timeout(TimeoutConfig.EXTRACT_RECIPE_INFO)
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
    user_prompt = read_prompt_files("prt_analyRecipe_user.txt", **replacements)
    system_prompt = read_prompt_files("prt_analyRecipe_system.txt", **replacements)
        
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
                "effort": "medium",
                "summary": "auto"
            },
            tools=[],
            store=True
        )
        
        # Log successful OpenAI response (info level - using standard logger)
        #logging.getLogger(__name__).info(f"OpenAI response received successfully", extra={"has_error": OpenAIresponse.error is not None})
        
        if OpenAIresponse.error is None:
            # 1) Prova proprietà comoda se presente
            output_text = getattr(OpenAIresponse, "output_text", None)
            if output_text:
                try:
                    return json.loads(output_text)
                except Exception as parse_error:
                    # Aumentato limite per debug - mantieni primi 500 caratteri + lunghezza totale
                    text_preview = str(output_text)[:500] + (f"... [troncato, lunghezza totale: {len(str(output_text))}]" if len(str(output_text)) > 500 else "")
                    error_logger.log_error("json_parse_output_text", "Failed to parse output_text as JSON", {"output_text": text_preview})

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
        # Log più dettagliato per debug del troncamento
        audio_preview = recipe_audio_text[:200] + f"... [tot: {len(recipe_audio_text)} chars]" if recipe_audio_text and len(recipe_audio_text) > 200 else recipe_audio_text or ""
        caption_preview = recipe_caption_text[:200] + f"... [tot: {len(recipe_caption_text)} chars]" if recipe_caption_text and len(recipe_caption_text) > 200 else recipe_caption_text or ""
        
        context = {
            "audio_text_length": len(recipe_audio_text) if recipe_audio_text else 0,
            "caption_text_length": len(recipe_caption_text) if recipe_caption_text else 0,
            "ingredients_count": len(ingredients) if isinstance(ingredients, list) else 0,
            "actions_count": len(actions) if isinstance(actions, list) else 0,
            "audio_preview": audio_preview,
            "caption_preview": caption_preview
        }
        
        # Classifica errore OpenAI se è un errore API
        if isinstance(e, (openai.RateLimitError, openai.AuthenticationError, openai.APIError)):
            openai_error = classify_openai_error(e, "extract_recipe_info", context)
            error_logger.log_exception("extract_recipe_info", openai_error, context)
            raise openai_error
        
        error_logger.log_exception("extract_recipe_info", e, context)
        raise  # Preserva stack trace originale

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_not_exception_type((QuotaExceededError, InvalidAPIKeyError, OpenAIError))
)
@timeout(TimeoutConfig.WHISPER_TRANSCRIPTION)
async def whisper_speech_recognition(audio_file_path: str, language: str) -> str:
    # Calcola timeout dinamico basato su dimensione file
    file_size_bytes = os.path.getsize(audio_file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    adjusted_timeout = TimeoutConfig.adjust_for_file_size(
        TimeoutConfig.WHISPER_TRANSCRIPTION, file_size_mb
    )
    
    with TimeoutContext("whisper_transcription", adjusted_timeout):
        try:
            # Leggi il contenuto del file e ottieni informazioni prima del thread async
            with open(audio_file_path, "rb") as audio_file:
                # Controlla la dimensione del file audio in KB
                audio_file.seek(0, 2)  # spostati alla fine del file
                file_size_bytes = audio_file.tell()
                audio_file.seek(0)     # torna all'inizio del file
                file_size_kb = file_size_bytes / 1024
                
                # Leggi tutto il contenuto del file in memoria
                audio_content = audio_file.read()
            
            # Crea un file-like object dal contenuto per evitare problemi con file descriptors
            import io
            # Usa context manager per garantire chiusura del buffer
            with io.BytesIO(audio_content) as audio_buffer:
                audio_buffer.name = audio_file_path  # Aggiungi il nome per compatibility
                
                # Ora esegui la trascrizione con il buffer in memoria
                transcription = await asyncio.to_thread(
                    openAIclient.audio.transcriptions.create,
                    model=OPENAI_TRANSCRIBE_MODEL,
                    file=audio_buffer,
                    language=language,
                )
            
            # Log successful transcription (info level) con anteprima del testo
            import logging
            text_preview = transcription.text[:200] + (f"... [continua per altri {len(transcription.text)-200} caratteri]" if len(transcription.text) > 200 else "") if transcription.text else ""
            logging.getLogger(__name__).info(f"Speech recognition completed successfully", extra={
                "audio_file": audio_file_path,
                "file_size_kb": file_size_kb,
                "file_size_mb": file_size_mb,
                "adjusted_timeout": adjusted_timeout,
                "language": language,
                "transcription_length": len(transcription.text) if transcription.text else 0,
                "transcription_preview": text_preview
            })
            
            return transcription.text
        except FileNotFoundError as e:
            error_logger.log_exception("whisper_file_not_found", e, {"audio_file_path": audio_file_path, "language": language})
            raise  # Preserva stack trace originale
        except Exception as e:
            context = {
                "audio_file_path": audio_file_path,
                "language": language,
                "file_size_mb": file_size_mb,
                "adjusted_timeout": adjusted_timeout
            }
            
            # Classifica errore OpenAI se è un errore API
            if isinstance(e, (openai.RateLimitError, openai.AuthenticationError, openai.APIError)):
                openai_error = classify_openai_error(e, "whisper_speech_recognition", context)
                error_logger.log_exception("whisper_speech_recognition", openai_error, context)
                raise openai_error
            
            error_logger.log_exception("whisper_speech_recognition", e, context)
            raise  # Preserva stack trace originale

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_not_exception_type((QuotaExceededError, InvalidAPIKeyError, OpenAIError))
)
@timeout(TimeoutConfig.GENERATE_IMAGES)
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
    
    tipologiaImmagin = [{
        "type": "copertina",
        "testo":  " ".join([p for p in [title, description] if p])
    }]
    
    '''
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
     image_prompt = read_prompt_files("prt_imgRecipe_user.txt", **replacements)

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
                    # Usa context manager per garantire chiusura connessione HTTP
                    with requests.get(url_val, timeout=30, stream=True) as resp:
                        resp.raise_for_status()
                        image_bytes = resp.content
                else:
                    raise ValueError("Elemento immagine privo di 'b64_json' e 'url'")

                out_path = os.path.join(image_folder, f"image_{img['type']}_{idx+1}.jpg")
                with open(out_path, "wb") as f:
                    f.write(image_bytes)
                saved_paths.append(ensure_media_web_path(out_path))
                # Log successful image save (info level)
                import logging
                logging.getLogger(__name__).info(f"Image saved successfully", extra={
                    "output_path": out_path,
                    "image_type": img["type"],
                    "image_index": idx+1
                })

            all_saved_paths.extend(saved_paths)
        except Exception as e:
            error_logger.log_exception("image_save", e, {"shortcode": shortcode, "image_type": img["type"]})
            raise

     except Exception as e:
        context = {"shortcode": shortcode, "recipe_title": ricetta.get("title", ""), "image_type": img["type"]}
        
        # Classifica errore OpenAI se è un errore API
        if isinstance(e, (openai.RateLimitError, openai.AuthenticationError, openai.APIError)):
            openai_error = classify_openai_error(e, "generate_recipe_images", context)
            error_logger.log_exception("generate_recipe_images", openai_error, context)
            raise openai_error
        
        error_logger.log_exception("generate_recipe_images", e, context)
        raise  # Preserva stack trace originale

    return all_saved_paths
