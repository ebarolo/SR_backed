from typing import List, Dict, Any, Optional
import uuid as uuid_lib

import logging

from config import (WCD_URL, WCD_API_KEY, ELYSIA_COLLECTION_NAME, ELYSIA_AVAILABLE, OPENAI_API_KEY)
from logging_config import get_error_logger, clear_error_chain
from utility import nfkc, lemmatize_it, remove_stopwords_spacy
from models import RecipeDBSchema

from elysia import configure
from elysia.util.client import ClientManager
from elysia import preprocess
from elysia import preprocessed_collection_exists

from elysia import Tree

import weaviate.classes.config as wvc

error_logger = get_error_logger(__name__)

def add_recipes_elysia(recipe_data: RecipeDBSchema):
    try:
        configure(
            wcd_url=WCD_URL,
            wcd_api_key=WCD_API_KEY,
            base_model="gpt-4.1",
            base_provider="openai",
            complex_model="gpt-4.1",
            complex_provider="openai",
            openai_api_key=OPENAI_API_KEY
        )
        status = False
        client_manager = ClientManager()

        with client_manager.connect_to_client() as client:
            # Usa un nome valido per la collection (senza trattini)
            collection_name = "Recipes"
            if client.collections.exists(collection_name):
                print(f"Collection '{collection_name}' already exists")
                # Opzionale: elimina la collection esistente per ricrearla
                # client.collections.delete(collection_name)
            else:
                client.collections.create(collection_name)
                print(f"Collection '{collection_name}' created successfully")

            recipe_collection = client.collections.get(collection_name)

            for recipe in recipe_data:
                try:           
                    # Processa ingredienti
                    ingr_lem = []
                    for ingredient in recipe_data.ingredients:
                        i_n = nfkc(ingredient.name)
                        i_s = remove_stopwords_spacy(i_n)
                        ingr_lem.append(i_s)
                    cats = [nfkc(x) for x in recipe_data.category]
                        
                    # Crea testo per il documento
                    document_text = (f"Titolo: {recipe_data.title}\n"
                                           f"Descrizione: {recipe_data.description}\n"
                                           f"Ingredienti: {'; '.join(ingr_lem)}\n"
                                           f"Categoria: {'; '.join(cats)}\n"
                        )

                    # Prepara i dati per Weaviate
                    recipe_object = {
                            "title": recipe_data.title,
                            "description": recipe_data.description,
                            "ingredients": '; '.join(ingr_lem),
                            "category": cats,  # Usa categorie processate, non ingredienti
                            "cuisine_type": recipe_data.cuisine_type or "",
                            "diet": recipe_data.diet or "",
                            "technique": recipe_data.technique or "",
                            "language": recipe_data.language,
                            "shortcode": recipe_data.shortcode,
                            "cooking_time": recipe_data.cooking_time or 0,
                            "preparation_time": recipe_data.preparation_time or 0,
                            #"document_text": document_text
                        }
                        
                    # Genera UUID valido dal shortcode
                    recipe_uuid = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, recipe_data.shortcode))
                    logging.debug(f"Recipe {recipe_data.shortcode}: UUID generato = {recipe_uuid}")
                        
                    # Verifica se esiste già
                    exists = recipe_collection.data.exists(recipe_uuid)
                    logging.debug(f"Recipe {recipe_data.shortcode}: esiste già = {exists}")
                    
                    if exists:   
                        recipe_collection.data.update(recipe_uuid)
                        logging.info(f"✅ Recipe {recipe_data.shortcode} aggiornata con successo")
                    else:
                        recipe_collection.data.insert(recipe_object)
                        logging.info(f"✅ Recipe {recipe_data.shortcode} inserita con successo")
                    
                except Exception as e:
                    logging.error(f"❌ Errore inserimento recipe {recipe_data.shortcode}: {str(e)}")
                    error_logger.log_exception("add_recipe_elysia", e, {
                        "shortcode": recipe_data.shortcode,
                        "title": recipe_data.title,
                        "ingredients_count": len(recipe_data.ingredients),
                        "categories_count": len(recipe_data.category)
                    })
            
            # Preprocessa la collection dopo aver inserito tutte le ricette
            respPreprocess = preprocess(collection_name)
            logging.info(f"✅ Collection pre-processata con successo")
            status = True
    except Exception as e:
        logging.error(f"❌ Errore pre-processing collection: {str(e)}")
        error_logger.log_exception("add_recipes_elysia", e, {})
        status = False
    finally:
        client_manager.close()
        return status


def search_recipes_elysia(query: str, limit: int = 10):
    try:
        configure(
            wcd_url=WCD_URL,
            wcd_api_key=WCD_API_KEY,
            base_model="gpt-4.1",
            base_provider="openai",
            complex_model="gpt-4.1",
            complex_provider="openai",
            openai_api_key=OPENAI_API_KEY
        )

        if not preprocessed_collection_exists(ELYSIA_COLLECTION_NAME):
            logging.info("Collection non pre-processata")
            preprocess(ELYSIA_COLLECTION_NAME)

        tree = Tree()
        risposta, oggetti = tree(
            query,
            collection_names=[ELYSIA_COLLECTION_NAME]
        )
       
        return risposta, oggetti

    except Exception as e:
        error_logger.log_exception("ERROR search_recipe_elysia", e, {
            "risposta": None,
            "oggetti": None
        })
        return None, None