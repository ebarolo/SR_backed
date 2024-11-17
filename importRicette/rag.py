import logging
import json
import requests

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)

def saveRecipeInRabitHole(recipeJSON, recipeTXT):
  url = "http://localhost:1865/rabbithole/"
    
  content_type = "text/plain"
  file_name = f"{recipeJSON['titolo']}.txt"
    
  files = {"file": (file_name, recipeTXT, content_type)}
    
  logger.info(f"files: {files}")

  metadata = {
        "sorgente": "import_ricette",
        "titolo": recipeJSON['titolo'],
        "categoria": recipeJSON['categoria'],
        "tempo_di_preparazione": recipeJSON['tempo_di_preparazione'],
        "tempo_cottura": recipeJSON['tempo_cottura'],
        "ingredienti": recipeJSON['ingredienti'],
        "preparazione": recipeJSON['preparazione'],
        "ricetta_audio": recipeJSON['ricetta_audio'],
        "ricetta_caption": recipeJSON['ricetta_caption'],
        "consigli_dello_chef": recipeJSON['consigli_dello_chef'],
    }
  
  logger.info(f"metadata: {metadata}")

  payload = {
        "metadata": json.dumps(metadata)
    }
  
  logger.info(f"payload: {payload}")
  
  try:
      response_RabitHole = requests.post(
        url,
        files=files,
        data=payload
     )
      logger.info(f"response_RabitHole: {str(response_RabitHole)}")
      return response_RabitHole
  except Exception as e:
     logger.error(f"error response_RabitHole {e}")
     raise