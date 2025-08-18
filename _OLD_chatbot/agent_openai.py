import os
from config import openAIclient,MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, MONGODB_VECTOR_SEARCH_INDEX_NAME, EMBEDDING_PATH, EMBEDDING_MODEL, SPACY_MODEL_NAME
from utility import logger

async def search_recipes(request: QueryRequest):

# Definizione della funzione di ricerca per il modello OpenAI (function calling schema)
    function_def = {
    "name": "search_recipes",
    "description": "Ricerca ricette nel database in base a criteri (es. ingrediente, categoria, tag, titolo).",
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Categoria del piatto da cercare (es. antipasto, primo, secondo, dolce)"
            },
            "ingredient": {
                "type": "string",
                "description": "Ingrediente da includere nella ricetta (es. rana pescatrice, pomodoro)"
            },
            "tag": {
                "type": "string",
                "description": "Tag o caratteristica della ricetta (es. vegan, piccante, veloce)"
            },
            "title": {
                "type": "string",
                "description": "Parola chiave contenuta nel titolo della ricetta"
            }
        },
        "required": []  # tutti i parametri sono opzionali, il modello deciderà quali usare
    }
}

    user_query = request.query  # estrai la query testuale dal payload
    # Chiamata all'API OpenAI per interpretare la query dell'utente
    try:
        ai_response = openAIclient.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",  # oppure "gpt-4-0613" se disponibile
            messages=[{"role": "user", "content": user_query}],
            functions=[function_def],
            function_call="auto"  # lascia decidere al modello se e come usare la funzione
        )
    except Exception as e:
        # Gestisce errori di rete o API OpenAI
        raise HTTPException(status_code=500, detail=f"Errore nell'interpretazione della query: {str(e)}")
    
    # Estrae gli argomenti dal function call restituito dal modello (se presente)
    message = ai_response.choices[0].message  
    params = {}  # dizionario dei parametri estratti
    if message.get("function_call"):
        try:
            # La risposta contiene una chiamata di funzione con argomenti in formato JSON
            args_str = message["function_call"]["arguments"]
            params = json.loads(args_str)  # parsing da stringa JSON a dizionario
        except (json.JSONDecodeError, KeyError) as e:
            raise HTTPException(status_code=500, detail="Impossibile interpretare i parametri di ricerca dalla query.")
    # Se il modello non ha invocato la funzione (scenario raro dato il prompt), 'params' rimarrà vuoto (nessun filtro specifico).