from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from pydantic import BaseModel, HttpUrl, validator

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from models import RecipeDBSchema, Ingredient, RecipeResponse

from importRicette.saveRecipe import process_video
from utility import get_error_context, logger, clean_text
from DB.mongoDB import get_mongo_collection, get_db
from DB.embedding import get_embedding

from chatbot.natural_language_recipe_finder_llm import LLMNaturalLanguageProcessor, RecipeFinder
#from chatbot.agent import get_recipes
from config import MONGODB_URI
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# -------------------------------
# Schemi Pydantic
# -------------------------------

class VideoURL(BaseModel):
    url: HttpUrl
    
    @validator('url')
    def validate_url(cls, v):
        allowed_domains = ['youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 'tiktok.com']
        if not any(domain in str(v) for domain in allowed_domains):
            raise ValueError(f"URL non supportato. Dominio deve essere tra: {', '.join(allowed_domains)}")
        return v

# -------------------------------
# Inizializzazione FastAPI e Dependency per il DB
# -------------------------------
app = FastAPI(title="Backend Smart Recipe", version="0.5")
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount mediaRicette directory explicitly to ensure all dynamic subfolders are accessible
app.mount("/mediaRicette", StaticFiles(directory="static/mediaRicette"), name="mediaRicette")

#-------------------------------
# Endpoints API
# -------------------------------
# -------------------------------
@app.get("/")
async def root():
    # In un template reale useresti Jinja2 o un'altra template-engine
    return {
        "message": "Vai su /static/index.html per provare i file statici"
}

@app.post("/recipes/", response_model=RecipeDBSchema, status_code=status.HTTP_201_CREATED)
async def insert_recipe(video: VideoURL):
    url = str(video.url) # Manteniamo l'URL per i log
    try:
        recipe_data = await process_video(url)
        # logger.info(f"recipe_data: {recipe_data}") # recipe_data è complesso, loggato già in process_video
        if not recipe_data:
            error_context = get_error_context()
            logger.error(f"Impossibile elaborare il video dall'URL '{url}'. Nessun dato ricetta ricevuto da process_video. Contesto: {error_context}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, # Più specifico di BAD_REQUEST per dati non elaborabili
                detail=f"Impossibile elaborare il video dall'URL fornito. Nessun dato ricetta valido è stato ottenuto."
            )
        
        # Prepara i dati per l'embedding
        title_clean = clean_text(recipe_data.title)
        logger.info(f"Title clean: {title_clean}")
        category_clean = ' '.join([clean_text(cat) for cat in recipe_data.category])
        logger.info(f"Category clean: {category_clean}")
        steps_clean = ' '.join([clean_text(step) for step in recipe_data.recipe_step])
        logger.info(f"Steps clean: {steps_clean}")
        ingredients_clean = ' '.join([clean_text(ing.name) for ing in recipe_data.ingredients])
        logger.info(f"Ingredients clean: {ingredients_clean}")
        
        # Costruisci il testo per l'embedding con una struttura più semantica
        text_for_embedding = f"{title_clean}. Categoria: {category_clean}. Ingredienti: {ingredients_clean}"
        logger.info(f"Testo per embedding generato per ricetta (shortcode: {recipe_data.shortcode}). Lunghezza: {len(text_for_embedding)}")
        logger.info(f"{text_for_embedding}")
        embedding = get_embedding(text_for_embedding)
        if embedding is None:
            # Log dell'errore già fatto da get_embedding
            logger.error(f"Fallimento generazione embedding per ricetta '{recipe_data.title}' (shortcode: {recipe_data.shortcode}). L'inserimento non può procedere con l'embedding.")
            # Si potrebbe decidere di inserire comunque la ricetta senza embedding o sollevare errore.
            # Per ora, solleviamo un errore perché l'embedding è considerato cruciale.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore interno durante la generazione dell'identificativo semantico della ricetta."
            )

        doc = {
            "title": recipe_data.title,
            "category": recipe_data.category,
            "preparation_time": recipe_data.preparation_time,
            "cooking_time": recipe_data.cooking_time,
            "ingredients": [ing.model_dump() for ing in recipe_data.ingredients],
            "recipe_step": recipe_data.recipe_step,
            "description": recipe_data.description,
            "diet": recipe_data.diet,
            "technique": recipe_data.technique,
            "language": recipe_data.language,
            "chef_advise": recipe_data.chef_advise,
            "tags": recipe_data.tags,
            "nutritional_info": recipe_data.nutritional_info,
            "cuisine_type": recipe_data.cuisine_type,
            "ricetta_audio": recipe_data.ricetta_audio,
            "ricetta_caption": recipe_data.ricetta_caption,
            "shortcode": recipe_data.shortcode,
            "embedding": embedding if embedding is not None else None
        }
        mongo_coll = get_mongo_collection()
        try:
            mongo_coll.replace_one(
                {"shortcode": recipe_data.shortcode},
                doc,
                upsert=True
            )
            logger.info(f"Ricetta '{doc['title']}' (shortcode: {doc['shortcode']}) inserita/aggiornata in MongoDB con successo.")
        except Exception as db_exc:
            error_context = get_error_context()
            logger.error(f"Errore durante il salvataggio in MongoDB per ricetta '{doc['title']}' (shortcode: {doc['shortcode']}): {db_exc}. Contesto: {error_context}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante il salvataggio della ricetta nel database."
            )

        return RecipeDBSchema(
            title=doc["title"],
            category=doc["category"],
            preparation_time=doc["preparation_time"],
            cooking_time=doc["cooking_time"],
            ingredients=[Ingredient(**ing) for ing in doc["ingredients"]],
            recipe_step=doc["recipe_step"],
            description=doc["description"],
            diet=doc["diet"],
            technique=doc["technique"],
            language=doc["language"],
            chef_advise=doc["chef_advise"],
            tags=doc["tags"],
            nutritional_info=doc["nutritional_info"],
            cuisine_type=doc["cuisine_type"],
            ricetta_audio=doc["ricetta_audio"],
            ricetta_caption=doc["ricetta_caption"],
            shortcode=doc["shortcode"]
        )
    except HTTPException as e:
        # Rilancia le HTTPException specifiche già gestite o sollevate
        raise e
    except Exception as e:
        error_context = get_error_context() # Prende il contesto dell'eccezione corrente
        logger.error(f"Errore imprevisto durante l'inserimento della ricetta dall'URL '{url}': {str(e)}. Contesto: {error_context}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore interno del server durante l'elaborazione della tua richiesta."
        )

@app.get("/recipes/{recipe_id}", response_model=RecipeDBSchema)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    return ""

@app.get("/search/")
def search_recipes( query: str, limit: int = 10 ):
    '''
    # Inizializza componenti
    nlp_processor = LLMNaturalLanguageProcessor()
    recipe_finder = None
    try:
        logger.info(f"Ricevuta query: {query}")

        # Estrai entità dalla query usando LLM
        entities = nlp_processor.extract_entities(query)

        # Cerca ricette
        recipe_finder = RecipeFinder(MONGODB_URI)
        recipes = recipe_finder.search_recipes(entities, limit)
        
        # Converti ObjectId in string e prepara la risposta
        response_recipes = []
        for recipe in recipes:
            recipe['_id'] = str(recipe['_id'])
            # Gestisci campi mancanti con valori di default
            recipe_data = {
                '_id': recipe['_id'],
                'title': recipe.get('title', 'Senza titolo'),
                'description': recipe.get('description', ''),
                'category': recipe.get('category', []),
                'cuisine_type': recipe.get('cuisine_type', ''),
                'ingredients': recipe.get('ingredients', []),
                'preparation_time': recipe.get('preparation_time', 0),
                'cooking_time': recipe.get('cooking_time', 0),
                'tags': recipe.get('tags', []),
                'chef_advise': recipe.get('chef_advise'),
                'match_score': recipe.get('match_score', 0.0),
                'shortcode': recipe.get('shortcode', ''),
                'recipe_step': recipe.get('recipe_step', [])
            }
            response_recipes.append(RecipeResponse(**recipe_data))

        return response_recipes

    except Exception as e:
        logger.error(f"Errore durante la ricerca: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")
    '''
    '''
    try:
        logger.info(f"Ricerca avviata per query: '{query}'")
        recipes = get_recipes(query, k=3) # get_recipes ora gestisce i propri log ed errori
        if not recipes:
            logger.warning(f"Nessuna ricetta trovata per la query: '{query}'")
            # Non è un errore, restituisce semplicemente una lista vuota, HTTP 200.
        else:
            logger.info(f"Trovate {len(recipes)} ricette per la query: '{query}'")
        return recipes
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore imprevisto durante la ricerca di ricette per la query '{query}': {str(e)}. Contesto: {error_context}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server durante la ricerca delle ricette."
        )
    '''
# -------------------------------
# Endpoints per la validazione di stato e prova
# -------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)