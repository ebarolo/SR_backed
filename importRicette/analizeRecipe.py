# Importazione delle librerie necessarie
import os
import base64
import logging
import asyncio
import json
import re
from pydantic import BaseModel

from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI

class ingredient(BaseModel):
 nome:str
 qt:int
   
class Recipe(BaseModel):
  recipe_id: str
  title: str
  category: list[str]
  prepration_time: int
  cooking_time: int
  ingredients: ingredient
  prepration_step: list[str]
  chef_advise: str
  tags:list[str]
  nutritional_info:list[str]
  cuisine_type:str
  ricetta_audio:str
  ricetta_caption:str
  video:str
  error:str
  
OPENAI_API_KEY = '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'
OpenAIclient = OpenAI(api_key=OPENAI_API_KEY)

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)

def timeout(seconds):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Timeout dopo {seconds} secondi nella funzione {func.__name__}")
                raise
        return wrapper
    return decorator

# Funzione per convertire il testo in un dizionario
def testo_a_dizionario(testo):
    risultato = {}
    linee = testo.strip().split('\n')
    chiave_corrente = None
    valore_corrente = []
    for linea in linee:
        if not linea.strip():
            continue
        # Verifica se la linea è una chiave
        if re.match(r'^\w+:', linea):
            if chiave_corrente:
                risultato[chiave_corrente] = '\n'.join(valore_corrente).strip()
            chiave_corrente, resto = linea.split(':', 1)
            chiave_corrente = chiave_corrente.strip()
            valore_corrente = [resto.strip()]
        else:
            valore_corrente.append(linea.strip())
    if chiave_corrente:
        risultato[chiave_corrente] = '\n'.join(valore_corrente).strip()
    return risultato

def read_prompt_files(recipe_audio_text="", recipe_capiton_text="", ingredients=None, actions=None, file_name=""):
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
        base_path = os.path.join('static')
        
        # Leggi prompt_user.txt
        with open(os.path.join(base_path, file_name), 'r', encoding='utf-8') as file:
            user_prompt = file.read()
            
        # Leggi prompt_system.txt
        with open(os.path.join(base_path, 'prompt_system.txt'), 'r', encoding='utf-8') as file:
            system_prompt = file.read()
            
        # Converti gli array in stringhe
        ingredients_text = "\n".join(ingredients) if ingredients else ""
        actions_text = "\n".join(actions) if actions else ""
            
        # Sostituisci le variabili nel testo
        variables = {
            '{recipe_audio}': recipe_audio_text,
            '{recipe_caption}': recipe_capiton_text,
            '{ingredients}': ingredients_text,
            '{actions}': actions_text
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
        return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
     logger.error(f"Errore durante la codifica dell'immagine {image_path}: {str(e)}")
     raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(300)
async def analyze_recipe_frames(base64Frames):
 try:
  PROMPT_MESSAGES = [
    { "role": "system",
       "content": "You are an assistant expert in culinary image analysis. Your task is to identify ingredients and cooking actions from an image."
    },
    {
        "role": "user",
        "content": [
            "These are frames from a video recipe that I want to upload. Identify the visible ingredients and the actions that are executed. Provide the answer in JSON format with three keys: ‘ingredients’ , ‘actions’, description.",
            *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::50]),
        ],
    },
  ]
  #logger.info({PROMPT_MESSAGES})
  params = {
    "model": "gpt-4o-mini",
    "messages": PROMPT_MESSAGES,
    "max_tokens": 700,
   }

  result = await asyncio.to_thread(
     OpenAIclient.chat.completions.create(params)
   )

  logger.info(result.choices[0])
  return result.choices[0].message.content
 except Exception as e:
  logger.error(f"Errore durante l'analisi dei fotogrammi: {str(e)}")
  raise
 
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(90)  # 1 minuto e 30 secondi di timeout
async def extract_recipe_info(recipe_audio_text: str, recipe_caption_text: str, ingredients: any, actions: any):

    user_prompt, system_prompt = read_prompt_files(recipe_audio_text, recipe_caption_text, ingredients, actions, "prompt_user_TXT.txt")
    logger.info(f"user_prompt: {user_prompt}")
    logger.info(f"system_prompt: {system_prompt}")

    try:
      OpenAIresponse = OpenAIclient.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=Recipe,
            temperature=0.9
        )

      logger.info(f"OpenAIresponse: {str(OpenAIresponse.choices[0].message.content)}")
      return OpenAIresponse.choices[0].message.parsed
  
    except Exception as e:
      logger.error(f"Errore durante OpenAIresponse: {str(e)}")
      raise e
    
    ''''
    user_prompt, system_prompt = read_prompt_files(recipe_audio_text, recipe_caption_text, ingredients, actions, "prompt_user_JSON.txt")
    logger.info(f"user_prompt: {user_prompt}")
    logger.info(f"system_prompt: {system_prompt}")

    try:
     OpenAI_JSON = OpenAIclient.chat.completions.create(
      model="gpt-4o-2024-08-06",
      messages=[
       {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": system_prompt
        }
      ]
    },
       {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": user_prompt
        }
      ]
    },
      ],
      response_format={
    "type": "json_schema",
    "json_schema": {
      "name": "recipe_schema",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "titolo": {
            "type": "string",
            "description": "The title of the recipe."
          },
          "categoria": {
            "type": "string",
            "description": "The category of the recipe."
          },
          "tempo_di_preparazione": {
            "type": "string",
            "description": "Preparation time for the recipe."
          },
          "tempo_cottura": {
            "type": "string",
            "description": "Cooking time for the recipe."
          },
          "ingredienti": {
            "type": "array",
            "description": "List of ingredients required for the recipe.",
            "items": {
              "type": "string"
            }
          },
          "preparazione": {
            "type": "array",
            "description": "Step-by-step preparation instructions.",
            "items": {
              "type": "string"
            }
          },
          "consigli_dello_chef": {
            "type": "string",
            "description": "Tips from the chef related to the recipe."
          },
          "ricetta_audio": {
            "type": "string",
            "description": "Audio description of the recipe."
          },
          "ricetta_caption": {
            "type": "string",
            "description": "Caption or description of the recipe for sharing."
          },
          "video": {
            "type": "string",
            "description": "File path or URL of the instructional video."
          }
        },
        "required": [
          "titolo",
          "categoria",
          "tempo_di_preparazione",
          "tempo_cottura",
          "ingredienti",
          "preparazione",
          "consigli_dello_chef",
          "ricetta_audio",
          "ricetta_caption",
          "video"
        ],
        "additionalProperties": False
      }
    }
  },
      temperature=0.9,
      
     )
    
     logger.info(f"recipeJSON: {str(OpenAI_JSON.choices[0].message.content)}")

     try:
      recipeJSON = json.loads(OpenAI_JSON.choices[0].message.content)
      recipeJSON
     
     except json.JSONDecodeError:
      logger.error(f"OpenAI_JSON JSONDecodeError: {str(json.JSONDecodeError.msg)} at line {str(json.JSONDecodeError.lineno)} column {str(json.JSONDecodeError.colno)}")
     raise json.JSONDecodeError
    
    except Exception as e:
     logger.error(f"Errore durante OpenAIresponseJSON: {str(e)}")
     raise e
     '''
    
    
