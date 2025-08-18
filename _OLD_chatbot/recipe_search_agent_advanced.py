from openai import OpenAI
import os
from pymongo import MongoClient
from typing import List, Dict, Any, Optional
import json
import numpy as np
from dotenv import load_dotenv
from config import logger, OPENAI_MODEL, EMBEDDING_PATH, EMBEDDING_MODEL, MONGODB_VECTOR_SEARCH_INDEX_NAME

# Carica variabili d'ambiente
load_dotenv()

# Configurazione OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configurazione MongoDB Atlas
mongodb_uri = os.getenv("MONGODB_URI")
mongo_client = MongoClient(mongodb_uri)
db = mongo_client[os.getenv("MONGODB_DB", "")]
collection = db[os.getenv("MONGODB_COLLECTION", "")]

# Definizione delle funzioni disponibili per l'agent con ricerca avanzata
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": "Cerca ricette nel database MongoDB Atlas basandosi su vari criteri come categoria, ingredienti, titolo o descrizione",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "La categoria della ricetta (es. antipasto, primo, secondo, dolce)"
                    },
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Lista di ingredienti da cercare nelle ricette"
                    },
                    "title_contains": {
                        "type": "string",
                        "description": "Testo da cercare nel titolo della ricetta"
                    },
                    "description_contains": {
                        "type": "string",
                        "description": "Testo da cercare nella descrizione della ricetta"
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Tag associati alla ricetta"
                    },
                    "technique": {
                        "type": "string",
                        "description": "Tecnica di cottura utilizzata"
                    },
                    "max_total_time": {
                        "type": "integer",
                        "description": "Tempo totale massimo (preparazione + cottura) in minuti"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search_recipes",
            "description": "Cerca ricette usando la ricerca semantica basata su embeddings. Utile per query più complesse o naturali.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La query di ricerca in linguaggio naturale"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Numero massimo di risultati da restituire (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recipe_details",
            "description": "Ottiene i dettagli completi di una ricetta specifica",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {
                        "type": "string",
                        "description": "L'ID della ricetta da recuperare"
                    },
                    "include_audio": {
                        "type": "boolean",
                        "description": "Se includere il link audio della ricetta",
                        "default": False
                    }
                },
                "required": ["recipe_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filter_recipes_by_nutrition",
            "description": "Filtra le ricette in base alle informazioni nutrizionali",
            "parameters": {
                "type": "object",
                "properties": {
                    "nutritional_requirements": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Requisiti nutrizionali specifici (es. 'basso contenuto di grassi', 'alto contenuto proteico')"
                    }
                },
                "required": ["nutritional_requirements"]
            }
        }
    }
]

def generate_embedding(text: str) -> List[float]:
    """
    Genera un embedding per il testo dato usando OpenAI
    """
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def search_recipes(
    category: str = None,
    ingredients: List[str] = None,
    title_contains: str = None,
    description_contains: str = None,
    tags: List[str] = None,
    technique: str = None,
    max_total_time: int = None
) -> List[Dict[str, Any]]:
    """
    Cerca ricette nel database MongoDB in base ai criteri specificati
    """
    query = {}
    
    # Costruisci la query MongoDB
    if category:
        query["category"] = {"$in": [category.lower()]}
    
    if ingredients:
        # Cerca ricette che contengono tutti gli ingredienti specificati
        ingredient_conditions = []
        for ingredient in ingredients:
            ingredient_conditions.append({
                "ingredients.name": {"$regex": ingredient, "$options": "i"}
            })
        if ingredient_conditions:
            query["$and"] = ingredient_conditions
    
    if title_contains:
        query["title"] = {"$regex": title_contains, "$options": "i"}
    
    if description_contains:
        query["description"] = {"$regex": description_contains, "$options": "i"}
    
    if tags:
        query["tags"] = {"$in": tags}
    
    if technique:
        query["technique"] = {"$regex": technique, "$options": "i"}
    
    if max_total_time:
        query["$expr"] = {
            "$lte": [
                {"$add": ["$preparation_time", "$cooking_time"]},
                max_total_time
            ]
        }
    logger.info(f"Query: {query}")
    # Esegui la query
    results = list(collection.find(query).limit(10))
    
    # Formatta i risultati
    formatted_results = []
    for result in results:
        formatted_results.append({
            "_id": str(result["_id"]),
            "title": result.get("title", ""),
            "description": result.get("description", ""),
            "category": result.get("category", []),
            "ingredients": [f"{ing['qt']} {ing['um']} {ing['name']}" for ing in result.get("ingredients", [])],
            "total_time": result.get("preparation_time", 0) + result.get("cooking_time", 0),
            "technique": result.get("technique", ""),
            "tags": result.get("tags", [])
        })
    
    return formatted_results

def semantic_search_recipes(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Esegue una ricerca semantica usando gli embeddings
    """
    # Genera embedding per la query
    query_embedding = generate_embedding(query)
    
    # Pipeline di aggregazione per la ricerca vettoriale
    pipeline = [
        {
            "$vectorSearch": {
                "index": MONGODB_VECTOR_SEARCH_INDEX_NAME,  # Nome dell'indice vettoriale in MongoDB Atlas
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": limit * 10,
                "limit": limit
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "description": 1,
                "category": 1,
                "ingredients": 1,
                "preparation_time": 1,
                "cooking_time": 1,
                "tags": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    try:
        results = list(collection.aggregate(pipeline))
        
        # Formatta i risultati
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "description": result.get("description", ""),
                "category": result.get("category", []),
                "ingredients": [f"{ing['qt']} {ing['um']} {ing['name']}" for ing in result.get("ingredients", [])],
                "total_time": result.get("preparation_time", 0) + result.get("cooking_time", 0),
                "tags": result.get("tags", []),
                "relevance_score": round(result.get("score", 0), 4)
            })
        
        return formatted_results
    except Exception as e:
        # Se l'indice vettoriale non esiste, usa la ricerca testuale
        print(f"Errore nella ricerca vettoriale: {e}")
        return search_recipes(description_contains=query)

def get_recipe_details(recipe_id: str, include_audio: bool = False) -> Dict[str, Any]:
    """
    Ottiene i dettagli completi di una ricetta specifica
    """
    from bson import ObjectId
    
    try:
        result = collection.find_one({"_id": ObjectId(recipe_id)})
        if result:
            # Formatta il risultato completo
            formatted = {
                "_id": str(result["_id"]),
                "title": result.get("title", ""),
                "shortcode": result.get("shortcode", ""),
                "description": result.get("description", ""),
                "category": result.get("category", []),
                "cuisine_type": result.get("cuisine_type", ""),
                "diet": result.get("diet", ""),
                "ingredients": result.get("ingredients", []),
                "recipe_steps": result.get("recipe_step", []),
                "preparation_time": result.get("preparation_time", 0),
                "cooking_time": result.get("cooking_time", 0),
                "total_time": result.get("preparation_time", 0) + result.get("cooking_time", 0),
                "technique": result.get("technique", ""),
                "chef_advise": result.get("chef_advise", ""),
                "nutritional_info": result.get("nutritional_info", []),
                "tags": result.get("tags", []),
                "language": result.get("language", "")
            }
            
            if include_audio:
                formatted["audio_url"] = result.get("ricetta_audio", "")
                formatted["caption"] = result.get("ricetta_caption", "")
            
            return formatted
        else:
            return {"error": "Ricetta non trovata"}
    except Exception as e:
        return {"error": f"Errore nel recupero della ricetta: {str(e)}"}

def filter_recipes_by_nutrition(nutritional_requirements: List[str]) -> List[Dict[str, Any]]:
    """
    Filtra le ricette in base ai requisiti nutrizionali
    """
    query = {
        "nutritional_info": {
            "$all": nutritional_requirements
        }
    }
    
    results = list(collection.find(query).limit(10))
    
    formatted_results = []
    for result in results:
        formatted_results.append({
            "_id": str(result["_id"]),
            "title": result.get("title", ""),
            "description": result.get("description", ""),
            "nutritional_info": result.get("nutritional_info", []),
            "diet": result.get("diet", "")
        })
    
    return formatted_results

def execute_function(function_name: str, arguments: dict) -> Any:
    """
    Esegue la funzione richiesta con gli argomenti specificati
    """
    if function_name == "search_recipes":
        return search_recipes(**arguments)
    elif function_name == "semantic_search_recipes":
        return semantic_search_recipes(**arguments)
    elif function_name == "get_recipe_details":
        return get_recipe_details(**arguments)
    elif function_name == "filter_recipes_by_nutrition":
        return filter_recipes_by_nutrition(**arguments)
    else:
        return {"error": f"Funzione {function_name} non trovata"}

def search_with_agent(user_query: str, use_streaming: bool = False) -> str:
    """
    Utilizza l'agent OpenAI per interpretare la query dell'utente e cercare ricette
    """
    # Messaggio di sistema con più contesto
    system_message = """Sei un assistente culinario esperto che aiuta a cercare ricette in un database MongoDB.
    
    Quando l'utente cerca ricette:
    1. Se menziona una categoria specifica (antipasto, primo, secondo, dolce), usa il parametro 'category'
    2. Se menziona ingredienti specifici, usa il parametro 'ingredients'
    3. Per ricerche più generiche o complesse, considera di usare 'semantic_search_recipes'
    4. Se l'utente vuole dettagli su una ricetta specifica, usa 'get_recipe_details'
    
    Analizza sempre attentamente la richiesta per capire quali parametri utilizzare."""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_query}
    ]
    
    # Prima chiamata all'API
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=use_streaming
    )
    
    if use_streaming:
        # Gestione dello streaming (più complessa)
        return handle_streaming_response(response, messages)
    else:
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # Se l'agent ha richiesto di chiamare una funzione
        if tool_calls:
            messages.append(response_message)
            
            # Esegui tutte le function calls
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"\n🔧 Chiamata funzione: {function_name}")
                print(f"   Argomenti: {json.dumps(function_args, ensure_ascii=False, indent=2)}")
                
                # Esegui la funzione
                function_response = execute_function(function_name, function_args)
                
                print(f"   Risultati trovati: {len(function_response) if isinstance(function_response, list) else 1}")
                
                # Aggiungi la risposta della funzione ai messaggi
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response, ensure_ascii=False)
                })
            
            # Seconda chiamata all'API per ottenere la risposta finale
            second_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            
            return second_response.choices[0].message.content
        
        return response_message.content
