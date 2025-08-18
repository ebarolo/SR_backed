
from typing import List, Dict, Any, Optional
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from config import openAIclient, OPENAI_MODEL, MONGODB_DB, MONGODB_COLLECTION
from tenacity import retry, stop_after_attempt, wait_exponential

from utility import logger

class LLMNaturalLanguageProcessor:
    """Classe per processare query in linguaggio naturale usando LLM"""

    def __init__(self):
        self.model = OPENAI_MODEL
        logger.info(f"Inizializzato processore NLP con modello: {self.model}")

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Estrae JSON da un testo che potrebbe contenere altro contenuto"""
        import re
        
        # Cerca pattern JSON nel testo
        json_patterns = [
            r'\{[^{}]*\}',  # JSON semplice
            r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # JSON con oggetti annidati
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Prova a parsare il match come JSON
                    data = json.loads(match)
                    # Verifica che abbia almeno alcuni dei campi attesi
                    expected_fields = ['ingredients', 'category', 'tags']
                    if any(field in data for field in expected_fields):
                        return data
                except json.JSONDecodeError:
                    continue
        
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Estrae entità dalla query usando LLM"""
        try:
            system_prompt = """Sei un assistente specializzato nell'analisi di richieste di ricette culinarie.
            Il tuo compito è estrarre informazioni strutturate da query in linguaggio naturale italiano.
            
            IMPORTANTE: Devi restituire SOLO un JSON valido, senza testo aggiuntivo prima o dopo.
            Non includere spiegazioni, commenti o altro testo. Solo il JSON.
            
            La struttura JSON DEVE essere esattamente questa:
            {
                "ingredients": ["lista", "di", "ingredienti"],
                "category": "categoria_singola o null",
                "cuisine_type": "tipo_cucina o null",
                "tags": ["lista", "di", "tag"],
                "cooking_time": numero_minuti_max o null,
                "diet": "tipo_dieta o null",
                "difficulty": "facile/medio/difficile o null",
                "meal_type": "colazione/pranzo/cena/spuntino o null",
                "season": "stagione o null",
                "special_request": "richieste_speciali o null"
            }
            
            Note importanti:
            - Usa null per valori mancanti, non omettere i campi
            - cooking_time deve essere un numero o null, non una stringa
            - Tutti gli array devono contenere stringhe
            
            Categorie valide: antipasto, primo, secondo, contorno, dolce, bevanda
            Tipi di cucina: italiana, francese, cinese, giappoinese, mediterranea, internazionale, medioevale, moderna, tradizionale, etnica
            Diete: vegetariano, vegano, gluten-free, light, proteico, keto, paleo
            
            Interpreta anche richieste implicite. Ad esempio:
            - "piatto veloce" → cooking_time: 30
            - "ricetta facile" → difficulty: "facile", tags: ["facile"]
            - "per cena" → meal_type: "cena"
            - "estivo" → season: "estate", tags: ["estivo"]
            
            RICORDA: Restituisci SOLO il JSON, nient'altro."""

            user_prompt = f"Analizza questa richiesta di ricetta e estrai le informazioni rilevanti: '{query}'"

            OpenAIresponse = openAIclient.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_output_tokens=500,
                store=False)

            # Estrai e parsa la risposta JSON
            if OpenAIresponse.error is None:
                # Parse the response into a RecipeSchema object
                logger.info(f"OpenAIresponse: {OpenAIresponse}")
                message_items = [item for item in OpenAIresponse.output if hasattr(item, "content")]
                if not message_items:
                    raise ValueError("No valid output message in OpenAIresponse")
                response_content = message_items[0].content[0]

                # Log the raw response content for debugging
                logger.debug(f"Raw response_content type: {type(response_content)}")
                logger.debug(f"Raw response_content: {response_content}")
                
                # Extract text content
                if isinstance(response_content, str):
                    json_string = response_content
                elif hasattr(response_content, "text"):
                    json_string = response_content.text
                else:
                    json_string = str(response_content)
                
                # Log the JSON string before parsing
                logger.info(f"JSON string to parse: {json_string}")
                
                try:
                    entities = json.loads(json_string)
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON: {json_string}")
                    logger.error(f"JSON error details: {je}")
                    
                    # Prova a estrarre JSON dal testo
                    logger.info("Tentativo di estrazione JSON dal testo...")
                    entities = self._extract_json_from_text(json_string)
                    
                    if entities is None:
                        logger.error("Impossibile estrarre JSON valido dalla risposta")
                        raise je
                    else:
                        logger.info("JSON estratto con successo usando fallback")

                # Normalizza e valida le entità estratte
                entities = self._normalize_entities(entities)

                logger.info(f"Entità estratte da LLM: {entities}")
                return entities
            else:
                logger.error(f"Errore nella risposta OpenAI: {OpenAIresponse.error}")
                return self._get_empty_entities()

        except json.JSONDecodeError as e:
            logger.error(f"Errore nel parsing JSON da LLM: {e}")
            # Fallback a entità vuote
            return self._get_empty_entities()
        except Exception as e:
            logger.error(f"Errore nell'estrazione entità con LLM: {e}")
            return self._get_empty_entities()

    def _normalize_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizza e valida le entità estratte"""
        # Assicura che tutti i campi esistano
        normalized = self._get_empty_entities()

        # Copia valori validi
        if isinstance(entities.get('ingredients'), list):
            normalized['ingredients'] = [ing.lower() for ing in entities['ingredients'] if isinstance(ing, str)]

        if entities.get('category') and isinstance(entities['category'], str):
            normalized['category'] = entities['category'].lower()

        if entities.get('cuisine_type') and isinstance(entities['cuisine_type'], str):
            normalized['cuisine_type'] = entities['cuisine_type'].lower()

        if isinstance(entities.get('tags'), list):
            normalized['tags'] = [tag.lower() for tag in entities['tags'] if isinstance(tag, str)]

        if isinstance(entities.get('cooking_time'), (int, float)) and entities['cooking_time'] > 0:
            normalized['cooking_time'] = int(entities['cooking_time'])

        if entities.get('diet') and isinstance(entities['diet'], str):
            normalized['diet'] = entities['diet'].lower()

        # Campi aggiuntivi dal LLM
        for field in ['difficulty', 'meal_type', 'season', 'special_request']:
            if entities.get(field) and isinstance(entities[field], str):
                normalized[field] = entities[field].lower()

        return normalized

    def _get_empty_entities(self) -> Dict[str, Any]:
        """Ritorna struttura vuota delle entità"""
        return {
            'ingredients': [],
            'category': None,
            'cuisine_type': None,
            'tags': [],
            'cooking_time': None,
            'diet': None,
            'difficulty': None,
            'meal_type': None,
            'season': None,
            'special_request': None
        }

class RecipeFinder:
    """Classe per cercare ricette nel database MongoDB"""

    def __init__(self, connection_string: str):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[MONGODB_DB]
            self.collection = self.db[MONGODB_COLLECTION]
            # Test connessione
            self.client.admin.command('ping')
            logger.info("Connesso a MongoDB Atlas con successo")
        except ConnectionFailure as e:
            logger.error(f"Errore di connessione a MongoDB: {e}")
            raise

    def build_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Costruisce la query MongoDB basata sulle entità estratte"""
        query = {}
        conditions = []

        # Query per ingredienti (usando $all per AND logico)
        # Verifica se ci sono ingredienti specificati nella query
        if entities['ingredients']:
            # Lista per memorizzare le condizioni di ricerca per ogni ingrediente
            ingredient_conditions = []
            # Itera su ogni ingrediente nella lista
            for ingredient in entities['ingredients']:
                # Aggiunge una condizione di ricerca per l'ingrediente corrente
                # Usa regex case-insensitive per match parziali del nome dell'ingrediente
                ingredient_conditions.append({
                    'ingredients.name': {
                        '$regex': ingredient,  # Pattern di ricerca dall'ingrediente
                        '$options': 'i'        # Flag per case-insensitive
                    }
                })

            # Se sono state create condizioni per gli ingredienti
            if ingredient_conditions:
                # Aggiunge tutte le condizioni degli ingredienti alla lista principale delle condizioni
                conditions.extend(ingredient_conditions)
        # Query per categoria
        # Verifica se è presente una categoria nelle entità estratte
        if entities['category']:
            # Aggiunge una condizione di ricerca per la categoria
            # Usa regex case-insensitive per match parziali
            conditions.append({
                'category': {
                    '$regex': entities['category'],  # Pattern di ricerca dalla categoria estratta
                    '$options': 'i'                  # Flag per case-insensitive
                }
            })

        # Query per tipo di cucina
        if entities['cuisine_type']:
            conditions.append({
                'cuisine_type': {
                    '$regex': entities['cuisine_type'],
                    '$options': 'i'
                }
            })

        # Query per tempo di cottura
        if entities['cooking_time']:
            conditions.append({
                '$expr': {
                    '$lte': [
                        {'$add': ['$preparation_time', '$cooking_time']},
                        entities['cooking_time']
                    ]
                }
            })

        # Query per dieta
        if entities['diet']:
            conditions.append({
                'diet': {
                    '$regex': entities['diet'],
                    '$options': 'i'
                }
            })

        # Query per tags (include anche difficulty, season, etc.)
        tags_to_search = entities['tags'].copy()

        # Aggiungi tags basati su altri campi
        if entities['difficulty']:
            tags_to_search.append(entities['difficulty'])
        if entities['season']:
            tags_to_search.append(entities['season'])
        if entities['meal_type']:
            tags_to_search.append(entities['meal_type'])

        if tags_to_search:
            conditions.append({
                'tags': {
                    '$in': tags_to_search
                }
            })

        # Costruisci la query finale
        if conditions:
            if len(conditions) > 1:
                query['$and'] = conditions
            else:
                query = conditions[0]

        logger.info(f"Query MongoDB costruita: {query}")
        return query

    def search_recipes(self, entities: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Cerca ricette nel database"""
        try:
            # Se non ci sono criteri specifici, usa text search se disponibile
            if not any(v for v in entities.values() if v):
                logger.warning("Nessuna entità estratta, eseguo ricerca generica")
                # Prova a fare una ricerca testuale se c'è un indice
                recipes = list(self.collection.find().limit(limit))
            else:
                query = self.build_query(entities)
                recipes = list(self.collection.find(query).limit(limit * 2))  # Prendi più risultati per lo scoring

            # Calcola match score basato sulle entità trovate
            scored_recipes = []
            for recipe in recipes:
                score = self.calculate_match_score(recipe, entities)
                recipe['match_score'] = score
                scored_recipes.append(recipe)

            # Ordina per score e prendi i top N
            scored_recipes.sort(key=lambda x: x['match_score'], reverse=True)
            top_recipes = scored_recipes[:limit]

            logger.info(f"Trovate {len(top_recipes)} ricette con score > 0")
            return top_recipes

        except OperationFailure as e:
            logger.error(f"Errore nella query MongoDB: {e}")
            raise

    def calculate_match_score(self, recipe: Dict[str, Any], entities: Dict[str, Any]) -> float:
        """Calcola un punteggio di rilevanza per la ricetta"""
        score = 0.0
        max_score = 0.0

        # Score per ingredienti (35% del peso)
        if entities['ingredients']:
            max_score += 35
            recipe_ingredients = [ing['name'].lower() for ing in recipe.get('ingredients', [])]
            matched_ingredients = sum(1 for ing in entities['ingredients'] 
                                    if any(ing in r_ing for r_ing in recipe_ingredients))
            if entities['ingredients']:
                score += (matched_ingredients / len(entities['ingredients'])) * 35

        # Score per categoria (20% del peso)
        if entities['category']:
            max_score += 20
            recipe_categories = [cat.lower() for cat in recipe.get('category', [])]
            if entities['category'] in recipe_categories:
                score += 20

        # Score per tipo di cucina (15% del peso)
        if entities['cuisine_type']:
            max_score += 15
            if entities['cuisine_type'] in recipe.get('cuisine_type', '').lower():
                score += 15

        # Score per tags e attributi (15% del peso)
        all_entity_tags = entities['tags'].copy()
        if entities['difficulty']:
            all_entity_tags.append(entities['difficulty'])
        if entities['season']:
            all_entity_tags.append(entities['season'])
        if entities['meal_type']:
            all_entity_tags.append(entities['meal_type'])

        if all_entity_tags:
            max_score += 15
            recipe_tags = [tag.lower() for tag in recipe.get('tags', [])]
            matched_tags = sum(1 for tag in all_entity_tags if tag in recipe_tags)
            if all_entity_tags:
                score += (matched_tags / len(all_entity_tags)) * 15

        # Score per dieta (10% del peso)
        if entities['diet']:
            max_score += 10
            if entities['diet'] in recipe.get('diet', '').lower():
                score += 10

        # Score per tempo di cottura (5% del peso)
        if entities['cooking_time']:
            max_score += 5
            total_time = recipe.get('preparation_time', 0) + recipe.get('cooking_time', 0)
            if total_time > 0 and total_time <= entities['cooking_time']:
                score += 5

        # Bonus per corrispondenze multiple (fino a 10 punti extra)
        matches = sum([
            bool(entities['ingredients'] and matched_ingredients > 0),
            bool(entities['category'] and entities['category'] in recipe_categories),
            bool(entities['cuisine_type'] and entities['cuisine_type'] in recipe.get('cuisine_type', '').lower()),
            bool(all_entity_tags and matched_tags > 0),
            bool(entities['diet'] and entities['diet'] in recipe.get('diet', '').lower())
        ])

        if matches >= 3:
            score = min(100, score + (matches * 2))

        # Normalizza lo score
        return (score / max_score * 100) if max_score > 0 else 0.0
