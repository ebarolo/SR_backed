from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, HttpUrl, validator
from typing import Optional
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

import json
import uvicorn
# Import per integrazione con MongoDB e NLP
from sentence_transformers import SentenceTransformer
from models import RecipeDBSchema, Ingredient

from importRicette.saveRecipe import process_video
from utility import get_error_context, logger,get_embedding,get_mongo_collection,get_db
from chatbot.agent import get_recipes
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modello SQLAlchemy per la ricetta
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    recipe_step = Column(Text)
    description = Column(Text)
    ingredients = Column(Text)  # memorizzati come stringa in formato JSON
    preparation_time = Column(Integer)  # tempo in minuti
    cooking_time = Column(Integer)
    diet = Column(String)               # ad es. "vegano", "vegetariano", ecc.
    category = Column(String)           # ad es. "primo", "secondo", "dolce"
    technique = Column(String)          # ad es. "cottura al forno", "frittura"
    language = Column(String, default="it")
    chef_advise = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    nutritional_info = Column(String, nullable=True)
    cuisine_type = Column(String, nullable=True)
    ricetta_audio = Column(String, nullable=True)
    ricetta_caption = Column(String, nullable=True)
    ingredients_text = Column(String, nullable=True)
    shortcode = Column(String, nullable=True)

# Creazione delle tabelle nel database
#Base.metadata.create_all(bind=engine)

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

class SearchQuery(BaseModel):
    query: str
    diet: Optional[str] = None
    max_preparation_time: Optional[int] = None
    difficulty: Optional[str] = None

# -------------------------------
# Inizializzazione FastAPI e Dependency per il DB
# -------------------------------
app = FastAPI(title="Backend Smart Recipe", version="0.5")

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
        
        # Rimuoviamo le stop words e miglioriamo la struttura del testo per l'embedding
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        import re

        # Funzione per pulire il testo
        def clean_text(text):
            # Converti in minuscolo e rimuovi caratteri speciali
            text = re.sub(r'[^\w\s]', ' ', text.lower())
            # Tokenizza
            tokens = word_tokenize(text)
            # Rimuovi stop words
            stop_words = set(stopwords.words('italian'))
            filtered_tokens = [word for word in tokens if word not in stop_words]
            return ' '.join(filtered_tokens)

        # Prepara i dati per l'embedding
        title_clean = clean_text(recipe_data.title)
        logger.info(f"Title clean: {title_clean}")
        steps_clean = ' '.join([clean_text(step) for step in recipe_data.recipe_step])
        logger.info(f"Steps clean: {steps_clean}")
        ingredients_clean = ' '.join([clean_text(ing.name) for ing in recipe_data.ingredients])
        logger.info(f"Ingredients clean: {ingredients_clean}")
        
        # Costruisci il testo per l'embedding con una struttura più semantica
        text_for_embedding = f"ricetta {title_clean} preparazione {steps_clean} ingredienti {ingredients_clean}"
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
            "embedding": embedding
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
    try:
        # Nota: il codice originale usa SQLAlchemy (Recipe, db.query) ma gli altri endpoint e utility usano MongoDB.
        # Questo endpoint sembra incoerente. Assumendo che si voglia usare MongoDB come per l'inserimento.
        # Se si deve usare SQLAlqchemy, questa logica va rivista per connettersi a un DB SQL.
        # Per ora, commento la parte SQL e ipotizzo una ricerca su MongoDB per ID, sebbene l'ID sia autoincrementante SQL.
        # Questa parte necessita di chiarimenti sul DB da usare per la lettura.
        # Se l'ID è un ID MongoDB (ObjectId), la logica cambia. Se è un ID numerico univoco in MongoDB, serve un campo apposito.
        # Per coerenza con l'inserimento che usa `shortcode` come ID univoco e non `id` numerico per MongoDB:
        # Modifico l'endpoint per cercare per `shortcode` invece di `recipe_id` numerico, oppure aggiungo un campo ID a MongoDB.
        # Per ora, assumo che `recipe_id` sia in realtà uno `shortcode` (stringa).
        # Cambierò il tipo dell'argomento in path e il nome per chiarezza.
        # ROUTE MODIFICATA: @app.get("/recipes/by_shortcode/{shortcode}", response_model=RecipeDBSchema)
        # Per mantenere la route originale @app.get("/recipes/{recipe_id}" ...
        # Dovremmo chiarire come recipe_id (int) mappa a un documento MongoDB.
        # Mantenendo la firma originale ma cercando per un campo `id_sql` in MongoDB (ipotetico):

        mongo_coll = get_mongo_collection() # Usiamo MongoDB come nel resto dell'app
        # recipe_doc = mongo_coll.find_one({"id": recipe_id}) # Assumendo che ci sia un campo "id" numerico
                                                          # Questo è improbabile se l'ID SQL è autoincrement.
                                                          # Soluzione più probabile: l'endpoint GET /recipes/{id} usa SQL,
                                                          # mentre POST /recipes/ usa Mongo. Questo è strano.
                                                          # Per ora, lascio la logica SQL originale, ma evidenzio l'incoerenza.

        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first() # Logica SQL originale

        if not recipe:
            error_context = get_error_context()
            # Usiamo warning per risorse non trovate, che è comune.
            logger.warning(f"Ricetta non trovata con ID SQL {recipe_id}. Contesto: {error_context}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Ricetta con ID {recipe_id} non trovata."
            )
        
        # Se la ricetta viene da SQL, dobbiamo convertirla in RecipeDBSchema
        # Gli attributi devono corrispondere. `ingredients` in SQL è una stringa JSON.
        try:
            ingredients_list = json.loads(recipe.ingredients) if isinstance(recipe.ingredients, str) else recipe.ingredients
        except json.JSONDecodeError:
            logger.error(f"Formato JSON non valido per gli ingredienti della ricetta ID SQL {recipe_id}. Valore: '{recipe.ingredients}'", exc_info=True)
            ingredients_list = [] # Fallback a lista vuota

        return RecipeDBSchema(
            id=recipe.id, # Aggiungiamo id se fa parte dello schema di risposta
            title=recipe.title,
            recipe_step=recipe.recipe_step.splitlines() if recipe.recipe_step else [], # Esempio di trasformazione se necessario
            description=recipe.description,
            ingredients=[Ingredient(**ing) for ing in ingredients_list], # Assumendo che ingredients_list sia ora una lista di dict
            preparation_time=recipe.preparation_time,
            cooking_time=recipe.cooking_time,
            diet=recipe.diet,
            category=recipe.category,
            technique=recipe.technique,
            language=recipe.language,
            chef_advise=recipe.chef_advise,
            tags=recipe.tags.split(',') if recipe.tags else [],
            nutritional_info=recipe.nutritional_info, # Potrebbe necessitare di parsing se è JSON string
            cuisine_type=recipe.cuisine_type,
            ricetta_audio=recipe.ricetta_audio,
            ricetta_caption=recipe.ricetta_caption,
            shortcode=recipe.shortcode
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore imprevisto durante il recupero della ricetta SQL con ID {recipe_id}: {str(e)}. Contesto: {error_context}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno del server durante il recupero della ricetta con ID {recipe_id}."
        )

@app.get("/search/")
def search_recipes( query: str ):
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
# -------------------------------
# Endpoints per la validazione di stato e prova
# -------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}

# -------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)