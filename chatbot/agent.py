# Importazioni necessarie
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import List as PydanticList, Optional, Dict, Any # Rinominato List per evitare conflitti
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple, Optional
import re
import json
import spacy
from spacy.matcher import PhraseMatcher # Importa PhraseMatcher

from DB.embedding import get_embedding
from config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, MONGODB_VECTOR_SEARCH_INDEX_NAME, EMBEDDING_PATH, EMBEDDING_MODEL, SPACY_MODEL_NAME
from utility import logger

class QueryInterpreterNLPCulinary:
    """
    Interpreta le query degli utenti per la ricerca di ricette e costruisce query MongoDB.
    Utilizza:
    1. Un modello di embedding per la comprensione semantica generale.
    2. spaCy con un modello italiano avanzato (es. it_core_news_lg) per analisi NLP.
    3. PhraseMatcher di spaCy e gazetteer (liste di entità) specifici del dominio culinario.
    """

    def __init__(self, EMBEDDING_MODEL, MONGODB_VECTOR_SEARCH_INDEX_NAME, SPACY_MODEL_NAME ): # Modello spaCy più grande per l'italiano
        """
        Inizializza l'interprete caricando i modelli e configurando i gazetteer.

        Args:
            embedding_model_name (str): Nome del modello SentenceTransformer.
            spacy_model_name (str): Nome del modello spaCy per l'italiano (es. 'it_core_news_lg' o 'it_core_news_md').
        """
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Modello di embedding '{EMBEDDING_MODEL}' caricato con successo.")
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.info(f"Errore durante il caricamento del modello di embedding '{EMBEDDING_MODEL}': {e}")
            raise

        try:
            self.nlp = spacy.load(SPACY_MODEL_NAME)
            logger.info(f"Modello spaCy '{SPACY_MODEL_NAME}' caricato con successo.")
        except OSError:
            logger.info(f"ERRORE: Modello spaCy '{SPACY_MODEL_NAME}' non trovato.")
            logger.info(f"Si prega di scaricarlo eseguendo: python -m spacy download {SPACY_MODEL_NAME}")
            logger.info("In alternativa, si può provare con un modello più piccolo come 'it_core_news_md'.")
            raise
        except Exception as e:
            logger.info(f"Errore sconosciuto durante il caricamento del modello spaCy '{SPACY_MODEL_NAME}': {e}")
            raise

        self._setup_gazetteers_and_matchers()

    def _setup_gazetteers_and_matchers(self):
        """
        Configura i gazetteer (liste di termini specifici del dominio) e i PhraseMatcher di spaCy.
        Queste liste sono cruciali e dovrebbero essere il più complete possibile.
        """
        # Liste di termini specifici del dominio culinario.
        # NOTA: Queste sono liste di esempio e dovrebbero essere notevolmente ampliate.
        self.gazetteers_data = {
            "DISHES": [ # Nomi di piatti comuni
                "carbonara", "spaghetti alla carbonara", "amatriciana", "lasagne alla bolognese",
                "risotto ai funghi porcini", "tiramisù", "panna cotta", "pizza margherita",
                "ossobuco", "pasta e fagioli", "caprese", "parmigiana di melanzane",
                "pollo al curry", "sushi", "paella", "couscous"
            ],
            "MAIN_INGREDIENTS": [ # Ingredienti principali
                # Carni
                "pollo", "manzo", "maiale", "agnello", "tacchino", "vitello", "coniglio", "salsiccia", "guanciale", "pancetta", "prosciutto cotto", "prosciutto crudo",
                # Pesce e Frutti di Mare
                "salmone", "tonno", "merluzzo", "branzino", "orata", "gamberi", "gamberetti", "calamari", "cozze", "vongole", "rana pescatrice", "pesce spada", "sogliola", "polpo", "seppie",
                # Verdure e Ortaggi
                "pomodoro", "pomodori", "pomodorini", "zucchina", "zucchine", "melanzana", "melanzane", "peperone", "peperoni", "patata", "patate", "carota", "carote", "cipolla", "cipolle", "aglio",
                "spinaci", "broccoli", "cavolfiore", "asparagi", "fungo", "funghi", "funghi porcini", "funghi champignon",
                "zucca", "carciofi", "finocchi", "sedano", "porri", "radicchio", "lattuga", "rucola", "indivia",
                # Frutta
                "mela", "mele", "pera", "pere", "banana", "banane", "arancia", "arance", "limone", "limoni", "fragola", "fragole", "frutti di bosco", "mirtilli", "lamponi",
                "pesca", "pesche", "albicocca", "albicocche", "prugna", "prugne", "fico", "fichi", "uva", "avocado", "mango", "ananas", "cocco",
                # Latticini e Formaggi
                "latte", "panna", "yogurt", "burro", "mozzarella", "parmigiano", "pecorino", "gorgonzola",
                "ricotta", "mascarpone", "fontina", "taleggio", "scamorza", "feta", "cheddar",
                # Cereali e Legumi
                "pasta", "riso", "farro", "orzo", "quinoa", "couscous", "pane", "farina", "polenta",
                "fagioli", "ceci", "lenticchie", "piselli", "soia",
                # Altro
                "uovo", "uova", "cioccolato", "cioccolato fondente", "cioccolato al latte", "cacao", "caffè", "noce", "noci", "mandorla", "mandorle", "nocciola", "nocciole",
                "pistacchi", "pinoli", "olio d'oliva", "aceto balsamico", "vino bianco", "vino rosso", "birra",
                "basilico", "prezzemolo", "rosmarino", "salvia", "timo", "origano", "menta", "peperoncino", "curry", "paprika", "zenzero", "cannella", "vaniglia"
            ],
            "CATEGORIES": [ # Categorie di piatti
                "antipasto", "primo piatto", "secondo piatto", "contorno", "dolce", "dessert", "piatto unico", "bevanda",
                "zuppa", "minestra", "insalata", "panino", "focaccia", "pizza", "torta salata", "frittata", "spezzatino", "stufato", "arrosto"
            ],
            "DIETS": [ # Tipi di dieta
                "vegetariana", "vegetariano", "vegana", "vegano", "senza glutine", "gluten free",
                "senza lattosio", "pescetariana", "paleo", "chetogenica", "ipocalorica", "light"
            ],
            "CHARACTERISTICS": [ # Caratteristiche o tag descrittivi
                "veloce", "rapida", "facile", "semplice", "leggera", "economica", "estiva", "invernale", "autunnale", "primaverile",
                "tradizionale", "regionale", "classica", "cremosa", "croccante", "speziata", "piccante", "agrodolce",
                "per bambini", "gourmet", "rustica", "elegante", "sfiziosa", "fredda", "calda", "tiepida"
            ],
            "TECHNIQUES": [ # Tecniche di cottura o preparazione
                "al forno", "fritta", "grigliata", "lessa", "al vapore", "in umido", "saltata in padella", "stufata", "arrosto",
                "marinata", "ripiena", "cruda", "mantecata", "lievitata", "sott'olio", "sott'aceto"
            ]
        }

        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER") # Matcher case-insensitive

        for label, terms in self.gazetteers_data.items():
            patterns = [self.nlp.make_doc(term) for term in terms] # Crea Doc spaCy per ogni termine
            self.phrase_matcher.add(label, patterns) # Usa l'etichetta definita (es. "DISHES")

        # Lemmi da ignorare per l'estrazione dei "termini chiave" generici,
        # per evitare di catturare parole troppo comuni o già classificate.
        self.ignore_lemmas_for_key_terms = set([
            "ricetta", "cucina", "piatto", "menu", "portata", "modo", "tipo", "idea", "suggerimento", "consiglio",
            "tempo", "cottura", "preparazione", "persona", "porzione", "cosa", "qualcosa", "fame", "voglia",
            "buono", "delizioso", "ottimo", "gustoso", "bello", "squisito",
            "fare", "preparare", "cucinare", "mangiare", "trovare", "cercare", "volere", "potere", "suggerire", "dare"
        ])
        # Aggiunge dinamicamente i lemmi dei gazetteer per evitare che vengano estratti come "key_terms" separati
        for gaz_label, gaz_terms in self.gazetteers_data.items():
            for term_doc in self.nlp.pipe(gaz_terms): # Processa i termini del gazetteer
                for token in term_doc:
                    if not token.is_punct and not token.is_stop:
                        self.ignore_lemmas_for_key_terms.add(token.lemma_.lower())


    def _normalize_text_for_embedding(self, query: str) -> str:
        """Normalizza il testo della query specificamente per la generazione dell'embedding."""
        text = query.lower()
        text = re.sub(r"[^\w\s']", "", text) # Rimuove punteggiatura tranne apostrofi
        text = text.strip()
        return text

    def extract_entities_and_intent(self, user_query: str) -> Tuple[List[float], Dict[str, Any]]:
        """
        Estrae entità (filtri) usando spaCy, PhraseMatcher e gazetteer culinari.
        L'"intento" principale è implicitamente "trovare una ricetta".

        Args:
            user_query (str): La query dell'utente in linguaggio naturale.

        Returns:
            Tuple[List[float], Dict[str, Any]]:
                - Il vettore di embedding della query (basato su testo normalizzato).
                - Un dizionario di filtri estratti (es. {"category": ["dolce"], "key_terms": ["cioccolato fondente"]}).
        """
        normalized_text_for_embedding = self._normalize_text_for_embedding(user_query)
        logger.info(f"Normalized text for embedding: {normalized_text_for_embedding}")
        query_embedding = self.embedding_model.encode(normalized_text_for_embedding).tolist()

        doc = self.nlp(user_query) # Processa la query originale con spaCy per mantenere il contesto
        
        # Inizializza il dizionario dei filtri
        filters: Dict[str, List[str]] = {label.lower(): [] for label in self.gazetteers_data.keys()}
        filters["key_terms"] = [] # Per termini non catturati dai gazetteer principali

        # 1. Usa PhraseMatcher per identificare termini specifici del dominio dai gazetteer
        matches = self.phrase_matcher(doc)
        # Tiene traccia degli indici dei token già inclusi in un match del PhraseMatcher
        # per evitare di processarli nuovamente come "key_terms" generici.
        matched_token_indices = set()

        for match_id, start, end in matches:
            span = doc[start:end]  # Lo span di testo che ha prodotto il match
            label_str = self.nlp.vocab.strings[match_id]  # Etichetta (es. "DISHES", "MAIN_INGREDIENTS")
            
            # Aggiunge il testo matchato (in minuscolo) alla lista corrispondente nei filtri.
            # Si assicura che non ci siano duplicati nella lista.
            normalized_span_text = span.text.lower()
            filter_key = label_str.lower() # Es. "dishes", "main_ingredients"
            
            if filter_key in filters and normalized_span_text not in filters[filter_key]:
                filters[filter_key].append(normalized_span_text)

            # Segna i token di questo span come già processati
            for i in range(start, end):
                matched_token_indices.add(i)
        
        # 2. Estrazione di "key_terms" aggiuntivi (termini non coperti dal PhraseMatcher)
        # Questi potrebbero essere ingredienti specifici non presenti nei gazetteer,
        # aggettivi descrittivi particolari, o parti di nomi di piatti non riconosciuti.
        potential_phrase_tokens = []
        for i, token in enumerate(doc):
            if i in matched_token_indices: # Se il token fa già parte di un match, saltalo.
                if potential_phrase_tokens: # Se c'era una frase potenziale prima, finalizzala.
                    phrase_text = " ".join([t.text for t in potential_phrase_tokens]).strip()
                    if phrase_text and phrase_text.lower() not in [kt.lower() for kt in filters["key_terms"]]:
                        filters["key_terms"].append(phrase_text)
                    potential_phrase_tokens = []
                continue

            # Considera NOMI, NOMI PROPRI e AGGETTIVI come potenziali parti di termini chiave,
            # solo se non sono stop-words, punteggiatura, o lemmi da ignorare.
            if token.pos_ in ["NOUN", "PROPN", "ADJ"] and \
               not token.is_stop and \
               not token.is_punct and \
               len(token.lemma_) > 1 and \
               token.lemma_.lower() not in self.ignore_lemmas_for_key_terms:
                potential_phrase_tokens.append(token)
            else: # Se il token non è rilevante, finalizza la frase potenziale corrente.
                if potential_phrase_tokens:
                    phrase_text = " ".join([t.text for t in potential_phrase_tokens]).strip()
                    if phrase_text and phrase_text.lower() not in [kt.lower() for kt in filters["key_terms"]]:
                         filters["key_terms"].append(phrase_text)
                    potential_phrase_tokens = []
        
        if potential_phrase_tokens: # Aggiungi l'ultima frase potenziale se presente.
            phrase_text = " ".join([t.text for t in potential_phrase_tokens]).strip()
            if phrase_text and phrase_text.lower() not in [kt.lower() for kt in filters["key_terms"]]:
                filters["key_terms"].append(phrase_text)

        # Rinomina i filtri per coerenza con la pipeline MongoDB e la logica precedente
        # (es. "characteristics" -> "tags", "main_ingredients" e "dishes" potrebbero confluire in "key_terms" o essere usati separatamente)
        final_filters: Dict[str, Any] = {}
        if filters.get("categories"): final_filters["category"] = filters["categories"]
        if filters.get("diets"): final_filters["diet"] = filters["diets"]
        if filters.get("characteristics"): final_filters["tags"] = filters["characteristics"]
        if filters.get("techniques"): final_filters["technique"] = filters["techniques"]
        
        # Unisce dishes, main_ingredients e key_terms in un unico campo "key_query_terms" per la ricerca testuale,
        # mantenendo la distinzione se necessario per logiche di match più specifiche.
        # Per la pipeline MongoDB, spesso è utile avere una lista aggregata di termini chiave.
        all_key_terms = set()
        for key in ["dishes", "main_ingredients", "key_terms"]:
            for term in filters.get(key, []):
                all_key_terms.add(term.lower()) # Assicura minuscolo e unicità
        
        if all_key_terms:
            final_filters["key_query_terms"] = sorted(list(all_key_terms))
            # Stampa i termini chiave identificati per debug
            logger.info(f"Termini Chiave / Ingredienti / Piatti estratti (NLP+Gazetteer): {final_filters['key_query_terms']}")
        
        # Rimuove eventuali filtri che sono rimasti con liste vuote
        final_filters = {k: v for k, v in final_filters.items() if v}
        
        return query_embedding, final_filters


    def build_mongo_query_pipeline(self, query_embedding: List[float], filters: Dict[str, Any],
                                   MONGODB_VECTOR_SEARCH_INDEX_NAME,
                                   num_candidates: int = 150, # Aumentato leggermente per dare più spazio ai filtri
                                   top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Costruisce una pipeline di aggregazione MongoDB per la ricerca di ricette.

        Args:
            query_embedding (List[float]): Il vettore di embedding della query utente.
            filters (Dict[str, Any]): Dizionario di filtri estratti.
            vector_index_name (str): Nome dell'indice Atlas Vector Search.
            num_candidates (int): Numero di candidati per $vectorSearch.
            top_n (int): Numero massimo di risultati da restituire dopo tutti i filtri.

        Returns:
            List[Dict[str, Any]]: La pipeline di aggregazione MongoDB.
        """
        pipeline: List[Dict[str, Any]] = []

        # 1. Stadio $vectorSearch (se l'embedding è valido)
        # Questo stadio dovrebbe idealmente venire prima dei filtri $match più restrittivi
        # per permettere alla ricerca vettoriale di trovare candidati semanticamente simili.
        if query_embedding and len(query_embedding) == self.embedding_dim:
            vector_search_stage = {
                "$vectorSearch": {
                    "index": MONGODB_VECTOR_SEARCH_INDEX_NAME,
                    "path": "embedding", # Campo nel DB che contiene gli embedding delle ricette
                    "queryVector": query_embedding,
                    "numCandidates": num_candidates, # Numero di candidati iniziali da considerare
                    "limit": top_n * 3 # Restituisce più risultati iniziali per poi filtrarli
                                       # Questo valore (top_n * 3) è un'euristica, da aggiustare.
                }
            }
            pipeline.append(vector_search_stage)
        else:
            logger.info("Attenzione: embedding non valido o non fornito. Salto lo stadio $vectorSearch.")
            # Se non c'è vector search, la pipeline si baserà solo sui filtri $match.
        
        # 2. Stadio $match per applicare i filtri categorici e testuali estratti
        match_conditions_list = [] # Lista di condizioni da mettere in un $and implicito o esplicito

        # Filtri categorici (category, diet, tags, technique)
        # Assumiamo che i campi corrispondenti nel DB siano liste di stringhe o stringhe singole.
        # Per campi lista nel DB, `$in` verifica se almeno uno dei valori è presente.
        # Per campi lista nel DB, `$all` verifica se tutti i valori sono presenti.
        # La scelta tra `$in` e `$all` dipende dalla logica desiderata per quel filtro.

        if "category" in filters and filters["category"]:
            # Un utente potrebbe chiedere "pasta o risotto" (due categorie).
            # Se il campo 'category' nel DB è una stringa, `$in` funziona.
            # Se 'category' è una lista, `$in` verifica se l'array del DB contiene ALMENO UNO dei valori.
            match_conditions_list.append({"category": {"$in": filters["category"]}})
        
        if "diet" in filters and filters["diet"]:
            # Per la dieta, di solito si vuole che TUTTE le condizioni siano soddisfatte (es. "vegana" E "senza glutine").
            # Assumiamo che 'diet' nel DB sia una lista di tag dietetici.
            match_conditions_list.append({"diet": {"$all": filters["diet"]}})

        if "tags" in filters and filters["tags"]: # Caratteristiche
            # Anche per i tag/caratteristiche, spesso si vuole che TUTTI siano presenti.
            match_conditions_list.append({"tags": {"$all": filters["tags"]}})
            
        if "technique" in filters and filters["technique"]:
            # Per le tecniche, potrebbe essere sufficiente che ALMENO UNA sia presente.
            match_conditions_list.append({"technique": {"$in": filters["technique"]}})

        # Filtro basato sui "key_query_terms" (ingredienti, nomi di piatti, ecc.)
        # Questo è un filtro testuale. Se si ha un indice Atlas Search ($text), sarebbe preferibile.
        # Altrimenti, si usano regex, che possono essere meno performanti su grandi dataset.
        if "key_query_terms" in filters and filters["key_query_terms"]:
            # Cerchiamo che TUTTI i termini chiave siano presenti in ALMENO UNO dei campi specificati.
            # Questo crea una condizione AND per ogni termine chiave.
            # Ogni termine chiave, a sua volta, può essere trovato in OR tra titolo, descrizione o nomi ingredienti.
            for term in filters["key_query_terms"]:
                safe_term = re.escape(term) # Escape per caratteri speciali regex
                term_match_condition = {
                    "$or": [
                        {"title": {"$regex": safe_term, "$options": "i"}},
                        {"description": {"$regex": safe_term, "$options": "i"}},
                        {"ingredients.name": {"$regex": safe_term, "$options": "i"}} # Assumendo che ingredients sia una lista di oggetti con un campo 'name'
                    ]
                }
                match_conditions_list.append(term_match_condition)
        
        if match_conditions_list:
            # Se c'è solo una condizione, non serve $and. Se multiple, le combina con $and.
            match_stage = {"$match": {"$and": match_conditions_list} if len(match_conditions_list) > 1 else match_conditions_list[0]}
            pipeline.append(match_stage)
        
        # 3. Stadio $project (opzionale, per definire i campi di output e lo score)
        project_fields: Dict[str, Any] = {
            "_id": 0, "title": 1, "description": 1, "category": 1, "diet": 1,
            "tags": 1, "ingredients": 1, "recipe_step": 1, "technique": 1,
            "preparation_time": 1, "cooking_time": 1
        }
        # Aggiunge lo score solo se $vectorSearch è stato usato e la pipeline non è vuota.
        if pipeline and "$vectorSearch" in pipeline[0]:
            project_fields["searchScore"] = {"$meta": "vectorSearchScore"}
        
        pipeline.append({"$project": project_fields})

        # 4. Se $vectorSearch è stato usato, potremmo aver già limitato abbastanza.
        # Altrimenti, o se vogliamo un limite finale esatto dopo i filtri $match:
        if not (pipeline and "$vectorSearch" in pipeline[0] and pipeline[0]["$vectorSearch"]["limit"] == top_n):
             pipeline.append({"$limit": top_n})


        return pipeline

# Initialize the NLP interpreter globally, after the class is defined
interpreter_culinary = QueryInterpreterNLPCulinary(EMBEDDING_MODEL, MONGODB_VECTOR_SEARCH_INDEX_NAME,SPACY_MODEL_NAME)

def get_recipes(user_query: str, k: int = 3) -> PydanticList[Dict[str, Any]]:
    """
    Suggerisce ricette da MongoDB basate sulla query dell'utente, categoria e ingrediente specifico.
    """
    embedding_vec, extracted_fltrs = interpreter_culinary.extract_entities_and_intent(user_query)
    logger.info(f"Filtri Estratti (NLP Culinario): {extracted_fltrs}")
            
    mongo_db_pipeline = interpreter_culinary.build_mongo_query_pipeline(embedding_vec, extracted_fltrs, MONGODB_VECTOR_SEARCH_INDEX_NAME)
    logger.info(f"Pipeline MongoDB Generata (NLP Culinario): {mongo_db_pipeline}")
            

    results: PydanticList[Dict[str, Any]] = []
    mongo_client: Optional[MongoClient] = None

    try:
        # Imposta un timeout per la selezione del server per evitare blocchi indefiniti
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Verifica la connessione inviando un comando ping
        mongo_client.admin.command('ping')
        db = mongo_client[MONGODB_DB]
        collection = db[MONGODB_COLLECTION]

        # Pipeline di aggregazione MongoDB per la ricerca vettoriale
        # 1. $vectorSearch: trova i documenti semanticamente più vicini.
        # 2. $match: filtra ulteriormente i risultati in base a criteri specifici (categoria, ingrediente, lingua).
        # 3. $limit: limita il numero finale di risultati.
        # 4. $project: definisce i campi da restituire.
        '''
        vector_search_pipeline = [
            {
                "$vectorSearch": {
                    "index": MONGODB_VECTOR_SEARCH_INDEX_NAME, # Il nome del tuo indice di ricerca vettoriale
                    "path": "embedding",               # Il campo nel documento che contiene i vettori
                    "queryVector": query_embedding,    # Il vettore della query generato
                    "numCandidates": 200,              # Numero di candidati iniziali da considerare (aumenta per filtri $match stringenti)
                    "limit": 5                       # Numero massimo di risultati da restituire da questa fase
                }
            },
            {
                "$limit": k # Limita il numero finale di suggerimenti dopo il $match
            },
            {
                "$project": { # Seleziona i campi da restituire
                    "_id": 0, # Esclude l'ID di MongoDB per default
                    "title": 1,
                    "category":1,
                    "description": 1,
                    "ingredients": 1,
                    "recipe_step": 1,
                    "chef_advise": 1,
                    "shortcode": 1,
                    "ingredients": 1, # Può essere utile per visualizzare gli ingredienti specifici
                    "vector_score": {"$meta": "vectorSearchScore"} # Include il punteggio di similarità della ricerca vettoriale
                }
            }
        ]
        '''
        try:
            results = list(collection.aggregate(mongo_db_pipeline))
            logger.info(f"Ricerca vettoriale completata. Trovati {len(results)} risultati che soddisfano tutti i criteri.")
            if not results:
                logger.info(f"La ricerca vettoriale non ha prodotto risultati che soddisfano i criteri di $match specificati.")
        except OperationFailure as e:
            logger.error(f"Errore durante l'esecuzione della ricerca vettoriale: {e}")
            if "index not found" in str(e).lower() or "$vectorSearch" in str(e) and ("Unrecognized pipeline stage" in str(e) or "unknown operator" in str(e)):
                logger.error(f"L'indice di ricerca vettoriale '{MONGODB_VECTOR_SEARCH_INDEX_NAME}' potrebbe non esistere, non essere configurato correttamente,")
                logger.error("oppure la versione di MongoDB o la configurazione del cluster non supportano $vectorSearch.")
            else:
                logger.error("Si è verificato un problema con l'operazione di ricerca vettoriale.")
            results = [] # Assicura che i risultati siano una lista vuota in caso di errore
        except Exception as e: # Cattura altri possibili errori durante l'aggregazione
            logger.error(f"Errore imprevisto durante la pipeline di ricerca vettoriale: {e}")
            results = []

    except ConnectionFailure:
       logger.error(f"Errore: Impossibile connettersi a MongoDB a {MONGODB_URI}. Verifica l'URI e che il server sia in esecuzione.")
    except Exception as e:
        logger.error(f"Errore generico durante l'operazione con MongoDB: {e}")
    finally:
        if mongo_client:
            mongo_client.close()

    return results