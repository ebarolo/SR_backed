from openai import OpenAI
import os
from pymongo import MongoClient
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Configurazione OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configurazione MongoDB Atlas
mongodb_uri = os.getenv("MONGODB_URI")
mongo_client = MongoClient(mongodb_uri)
db = mongo_client[os.getenv("MONGODB_DB", "recipes")]
collection = db[os.getenv("MONGODB_COLLECTION", "")]

# Definizione delle funzioni disponibili per l'agent
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
                    "cuisine_type": {
                        "type": "string",
                        "description": "Tipo di cucina (es. italiana, francese, etc.)"
                    },
                    "diet": {
                        "type": "string",
                        "description": "Tipo di dieta (es. vegetariana, vegana, etc.)"
                    },
                    "max_cooking_time": {
                        "type": "integer",
                        "description": "Tempo massimo di cottura in minuti"
                    }
                },
                "required": []
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
                    }
                },
                "required": ["recipe_id"]
            }
        }
    }
]

def search_recipes(
    category: str = None,
    ingredients: List[str] = None,
    title_contains: str = None,
    description_contains: str = None,
    cuisine_type: str = None,
    diet: str = None,
    max_cooking_time: int = None
) -> List[Dict[str, Any]]:
    """
    Cerca ricette nel database MongoDB in base ai criteri specificati
    """
    query = {}
    
    # Costruisci la query MongoDB
    if category:
        query["category"] = {"$in": [category.lower()]}
    
    if ingredients:
        # Cerca ricette che contengono almeno uno degli ingredienti specificati
        ingredient_conditions = []
        for ingredient in ingredients:
            ingredient_conditions.append({
                "ingredients.name": {"$regex": ingredient, "$options": "i"}
            })
        if ingredient_conditions:
            query["$or"] = ingredient_conditions
    
    if title_contains:
        query["title"] = {"$regex": title_contains, "$options": "i"}
    
    if description_contains:
        query["description"] = {"$regex": description_contains, "$options": "i"}
    
    if cuisine_type:
        query["cuisine_type"] = {"$regex": cuisine_type, "$options": "i"}
    
    if diet:
        query["diet"] = diet
    
    if max_cooking_time:
        query["cooking_time"] = {"$lte": max_cooking_time}
    
    # Esegui la query
    results = list(collection.find(query).limit(10))
    
    # Converti ObjectId in stringa per la serializzazione JSON
    for result in results:
        result["_id"] = str(result["_id"])
        # Rimuovi il campo embedding per non appesantire la risposta
        result.pop("embedding", None)
    
    return results

def get_recipe_details(recipe_id: str) -> Dict[str, Any]:
    """
    Ottiene i dettagli completi di una ricetta specifica
    """
    from bson import ObjectId
    
    try:
        result = collection.find_one({"_id": ObjectId(recipe_id)})
        if result:
            result["_id"] = str(result["_id"])
            result.pop("embedding", None)
            return result
        else:
            return {"error": "Ricetta non trovata"}
    except Exception as e:
        return {"error": f"Errore nel recupero della ricetta: {str(e)}"}

def execute_function(function_name: str, arguments: dict) -> Any:
    """
    Esegue la funzione richiesta con gli argomenti specificati
    """
    if function_name == "search_recipes":
        return search_recipes(**arguments)
    elif function_name == "get_recipe_details":
        return get_recipe_details(**arguments)
    else:
        return {"error": f"Funzione {function_name} non trovata"}

def search_with_agent(user_query: str) -> str:
    """
    Utilizza l'agent OpenAI per interpretare la query dell'utente e cercare ricette
    """
    # Primo messaggio all'agent
    messages = [
        {
            "role": "system",
            "content": "Sei un assistente esperto di cucina che aiuta a cercare ricette in un database. Analizza la richiesta dell'utente e utilizza le funzioni disponibili per trovare le ricette più appropriate."
        },
        {
            "role": "user",
            "content": user_query
        }
    ]
    
    # Prima chiamata all'API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
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
            print(f"   Argomenti: {function_args}")
            
            # Esegui la funzione
            function_response = execute_function(function_name, function_args)
            
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

# Esempio di utilizzo
if __name__ == "__main__":
    # Query di esempio: "antipasto con rana pescatrice"
    query = "antipasto con rana pescatrice"
    
    print(f"🔍 Ricerca: {query}")
    print("-" * 50)
    
    result = search_with_agent(query)
    print(f"\n📋 Risultato:\n{result}") 