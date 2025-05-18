# main_chatbot.py

import os
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Any

# 1. Definizione dello schema dei dati (come fornito)
class Ingredient(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None

class RecipeDBSchema(BaseModel):
    title: str
    category: List[str]
    preparation_time: Optional[int] = None
    cooking_time: Optional[int] = None
    ingredients: List[Ingredient]
    recipe_step: List[str]
    description: str
    diet: Optional[str] = None
    technique: Optional[str] = None
    language: str
    chef_advise: Optional[str] = None
    tags: Optional[List[str]] = None
    nutritional_info: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    ricetta_audio: Optional[str] = None
    ricetta_caption: Optional[str] = None
    shortcode: str
    embedding: List[float] # Campo cruciale per la ricerca vettoriale

# 2. Classe Chatbot
class RecipeChatbot:
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str,
                 embedding_model_name: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
                 vector_index_name: str = "idx_recipe_embedding"): # Nome dell'indice vettoriale su Atlas
        """
        Inizializza il chatbot.
        Args:
            mongo_uri (str): Stringa di connessione a MongoDB Atlas.
            db_name (str): Nome del database.
            collection_name (str): Nome della collezione.
            embedding_model_name (str): Nome del modello SentenceTransformer.
            vector_index_name (str): Nome dell'indice di ricerca vettoriale creato in Atlas.
        """
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            # Verifica la connessione
            self.client.admin.command('ping')
            print("Connessione a MongoDB Atlas stabilita con successo.")
        except Exception as e:
            print(f"Errore fatale durante la connessione a MongoDB: {e}")
            print("Dettagli dell'errore:")
            print(f"  Tipo di errore: {type(e).__name__}")
            print(f"  Messaggio: {str(e)}")
            print("\nPossibili cause e soluzioni:")
            print("1. URI di connessione errato: controlla attentamente la stringa MONGO_URI.")
            print("2. Credenziali non valide: verifica utente e password.")
            print("3. Cluster non attivo o non raggiungibile: assicurati che il cluster Atlas sia operativo.")
            print("4. IP non autorizzato: aggiungi il tuo indirizzo IP attuale alla lista degli accessi IP in Atlas Network Access.")
            print("5. Problemi di rete/firewall: verifica che non ci siano blocchi sulla porta 27017 (o la porta usata).")
            print("6. Modulo dnspython non installato (necessario per 'mongodb+srv'): esegui 'pip install dnspython'.")
            raise

        try:
            self.embedding_model = SentenceTransformer(embedding_model_name)
            print(f"Modello di embedding '{embedding_model_name}' caricato con successo.")
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            print(f"Dimensione degli embedding generati dal modello: {self.embedding_dim}")
        except Exception as e:
            print(f"Errore durante il caricamento del modello di embedding '{embedding_model_name}': {e}")
            print("Assicurati che il nome del modello sia corretto e che tu abbia una connessione internet se il modello deve essere scaricato.")
            raise

        self.vector_index_name = vector_index_name
        print(f"Il chatbot utilizzerà l'indice vettoriale Atlas chiamato: '{self.vector_index_name}'.")
        print(f"Assicurati che questo indice esista nella collezione '{collection_name}' del database '{db_name}'.")
        print(f"L'indice deve essere configurato per il campo 'embedding' con {self.embedding_dim} dimensioni.")


    def get_embedding(self, text: str) -> List[float]:
        """
        Genera l'embedding per un testo dato.
        Args:
            text (str): Il testo da cui generare l'embedding.
        Returns:
            List[float]: Il vettore di embedding.
        """
        if not text or not isinstance(text, str):
            print("Attenzione: testo non valido fornito per l'embedding. Restituzione di un embedding nullo.")
            return [0.0] * self.embedding_dim # Ritorna un vettore nullo della dimensione corretta
        
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def find_similar_recipes(self, user_query: str, top_n: int = 3, candidate_limit: int = 100) -> List[Dict[str, Any]]:
        """
        Trova ricette simili basate sulla query dell'utente usando la ricerca vettoriale in MongoDB Atlas.
        Args:
            user_query (str): La domanda dell'utente in linguaggio naturale.
            top_n (int): Il numero massimo di ricette da restituire.
            candidate_limit (int): Il numero di candidati da considerare durante la ricerca (parametro numCandidates di $vectorSearch).
        Returns:
            List[Dict[str, Any]]: Una lista di dizionari, ognuno rappresentante una ricetta simile.
        """
        if not user_query.strip():
            print("Query utente vuota. Impossibile cercare.")
            return []
            
        query_embedding = self.get_embedding(user_query)

        # Pipeline di aggregazione per la ricerca vettoriale
        pipeline = [
            {
                '$vectorSearch': {
                    'index': self.vector_index_name, # Nome dell'indice vettoriale creato in Atlas
                    'path': 'embedding',             # Campo nel documento che contiene il vettore
                    'queryVector': query_embedding,  # Vettore della query dell'utente
                    'numCandidates': candidate_limit,# Numero di candidati da considerare
                    'limit': top_n                   # Numero di risultati da restituire
                }
            },
            { # Proietta i campi desiderati e il punteggio di similarità
                '$project': {
                    '_id': 0, # Esclude l'ID di MongoDB
                    'title': 1,
                    'description': 1,
                    'ingredients': 1,
                    'recipe_step': 1,
                    'preparation_time': 1,
                    'cooking_time': 1,
                    'category': 1,
                    'language': 1,
                    'score': { # Aggiunge il punteggio di similarità della ricerca vettoriale
                        '$meta': 'vectorSearchScore'
                    }
                }
            }
        ]

        try:
            results = list(self.collection.aggregate(pipeline))
            return results
        except Exception as e: # Specificamente pymongo.errors.OperationFailure per problemi con l'indice
            print(f"Errore durante l'esecuzione della ricerca vettoriale: {e}")
            print(f"Dettagli dell'errore: Tipo: {type(e).__name__}, Messaggio: {str(e)}")
            print("\nPossibili cause e soluzioni:")
            print(f"1. Indice vettoriale '{self.vector_index_name}' non esistente o non ancora pronto nella collezione '{self.collection.name}'.")
            print(f"   Verifica la sua esistenza e stato nella UI di Atlas (sezione 'Search').")
            print(f"2. Configurazione dell'indice errata: il path ('embedding') o numDimensions ({self.embedding_dim}) potrebbero non corrispondere.")
            print(f"3. Problemi di permessi utente per eseguire aggregazioni con $vectorSearch.")
            print(f"4. Versione del server MongoDB non compatibile con $vectorSearch (richiede Atlas).")
            return []

    def format_recipe_response(self, recipe: Dict[str, Any]) -> str:
        """
        Formatta una singola ricetta (recuperata da MongoDB) per la visualizzazione.
        Args:
            recipe (Dict[str, Any]): Dizionario contenente i dati di una ricetta.
        Returns:
            str: Stringa formattata con i dettagli della ricetta.
        """
        response_parts = []
        score = recipe.get('score')
        if score is not None:
             response_parts.append(f"\n--- Ricetta Trovata (Punteggio di similarità: {score:.4f}) ---")
        else:
            response_parts.append("\n--- Ricetta Trovata ---")

        response_parts.append(f"Titolo: {recipe.get('title', 'N/D')}")
        
        description = recipe.get('description')
        if description:
             response_parts.append(f"Descrizione: {description}")
        
        prep_time = recipe.get('preparation_time')
        cook_time = recipe.get('cooking_time')
        if prep_time is not None:
            response_parts.append(f"Tempo di preparazione: {prep_time} minuti")
        if cook_time is not None:
            response_parts.append(f"Tempo di cottura: {cook_time} minuti")

        ingredients_data = recipe.get('ingredients', [])
        if ingredients_data:
            response_parts.append("Ingredienti:")
            for ing_data in ingredients_data:
                name = ing_data.get('name', 'N/D')
                qty = ing_data.get('quantity', '')
                unit = ing_data.get('unit', '')
                response_parts.append(f"  - {name} {qty} {unit}".strip())
        
        steps = recipe.get('recipe_step', [])
        if steps:
            response_parts.append("Preparazione:")
            for i, step in enumerate(steps):
                response_parts.append(f"  {i+1}. {step}")
        
        response_parts.append("--------------------------------------")
        return "\n".join(response_parts)

    def ask(self, user_question: str) -> str:
        """
        Riceve una domanda dall'utente, cerca ricette simili e restituisce una risposta formattata.
        Args:
            user_question (str): La domanda dell'utente.
        Returns:
            str: La risposta del chatbot, contenente una o più ricette o un messaggio di cortesia.
        """
        print(f"\nRicerca per: '{user_question}'...")
        if not user_question.strip():
            return "Per favore, inserisci una domanda valida."
            
        # Per questo MVP, cerchiamo solo la ricetta più simile.
        # Si potrebbe estendere per restituirne multiple o per fare domande di chiarimento.
        recipes = self.find_similar_recipes(user_question, top_n=1)

        if not recipes:
            return "Mi dispiace, non sono riuscito a trovare una ricetta che corrisponda alla tua richiesta nel database."

        # Per MVP, restituiamo solo la prima ricetta trovata.
        best_recipe = recipes[0]
        return self.format_recipe_response(best_recipe)

# 3. Funzione per popolare dati di esempio (opzionale, per test)
def populate_sample_data(chatbot: RecipeChatbot, force_populate: bool = False):
    """
    Popola MongoDB con alcuni dati di esempio se la collezione è vuota o se force_populate è True.
    IMPORTANTE: Questo genererà embedding per i dati di esempio. In un'applicazione reale,
    gli embedding dovrebbero essere pre-generati e memorizzati durante l'ingestion dei dati.
    Args:
        chatbot (RecipeChatbot): Istanza del chatbot, usata per accedere alla collezione e al modello di embedding.
        force_populate (bool): Se True, cancella i dati esistenti prima di popolare.
    """
    collection = chatbot.collection
    
    if not force_populate and collection.count_documents({}) > 0:
        print(f"La collezione '{collection.name}' contiene già {collection.count_documents({})} documenti. Salto il popolamento di esempio.")
        # Controllo opzionale sulla dimensione degli embedding esistenti
        first_doc = collection.find_one({"embedding": {"$exists": True}})
        if first_doc and 'embedding' in first_doc and isinstance(first_doc['embedding'], list):
            existing_dim = len(first_doc['embedding'])
            if existing_dim != chatbot.embedding_dim:
                print(f"ATTENZIONE: La dimensione degli embedding esistenti ({existing_dim}) "
                      f"non corrisponde alla dimensione del modello attuale ({chatbot.embedding_dim}).")
                print("Questo potrebbe causare errori o risultati inattesi con la ricerca vettoriale.")
                print("Considera di rigenerare gli embedding per i dati esistenti o di aggiornare l'indice vettoriale.")
        return

    print(f"Inizio popolamento della collezione '{collection.name}' con dati di esempio...")
    
    sample_recipes_raw_data = [
        {
            "title": "Spaghetti alla Carbonara Autentica", "category": ["Pasta", "Piatto principale", "Cucina Romana"],
            "preparation_time": 10, "cooking_time": 15,
            "ingredients": [
                Ingredient(name="Spaghetti", quantity="320", unit="g").model_dump(),
                Ingredient(name="Guanciale", quantity="150", unit="g").model_dump(),
                Ingredient(name="Uova medie (solo tuorli)", quantity="4").model_dump(),
                Ingredient(name="Pecorino Romano DOP", quantity="50", unit="g").model_dump(),
                Ingredient(name="Pepe nero macinato fresco").model_dump(),
            ],
            "recipe_step": [
                "Tagliare il guanciale a dadini o listarelle spesse circa 1 cm.",
                "In una padella antiaderente, rosolare il guanciale a fuoco dolce senza aggiungere altri grassi, finché diventa croccante e dorato. Togliere il guanciale dalla padella e tenere da parte il grasso.",
                "In una ciotola, sbattere energicamente i tuorli con il Pecorino Romano grattugiato e abbondante pepe nero macinato fresco, fino ad ottenere una crema densa.",
                "Cuocere gli spaghetti in abbondante acqua leggermente salata (il guanciale e il pecorino sono già sapidi).",
                "Scolare la pasta al dente, conservando un mestolo di acqua di cottura.",
                "Versare gli spaghetti nella ciotola con la crema di tuorli e pecorino. Aggiungere il guanciale croccante e un po' del suo grasso. Mescolare rapidamente.",
                "Se necessario per raggiungere la cremosità desiderata, aggiungere poca acqua di cottura della pasta. La crema non deve 'cuocere' ma rimanere fluida.",
                "Servire immediatamente con un'ulteriore spolverata di Pecorino Romano e pepe nero."
            ],
            "description": "La vera ricetta della Carbonara, un pilastro della cucina italiana, cremosa e intensamente saporita grazie al guanciale e al pecorino.", 
            "language": "italiano", "shortcode": "carbonara_auth_01", "diet": "Non vegetariano", "cuisine_type": "Italiana",
            "tags": ["classico italiano", "roma", "guanciale", "pecorino", "pasta veloce"]
        },
        {
            "title": "Torta Margherita Soffice della Nonna", "category": ["Dolci", "Torte da colazione"],
            "preparation_time": 20, "cooking_time": 35,
            "ingredients": [
                Ingredient(name="Farina 00", quantity="125", unit="g").model_dump(), 
                Ingredient(name="Fecola di patate", quantity="125", unit="g").model_dump(),
                Ingredient(name="Zucchero semolato", quantity="200", unit="g").model_dump(), 
                Ingredient(name="Uova medie a temperatura ambiente", quantity="4").model_dump(),
                Ingredient(name="Burro fuso e intiepidito", quantity="80", unit="g").model_dump(), 
                Ingredient(name="Lievito in polvere per dolci", quantity="1", unit="bustina (16g)").model_dump(),
                Ingredient(name="Scorza grattugiata di 1 limone bio").model_dump(), 
                Ingredient(name="Un pizzico di sale").model_dump(),
                Ingredient(name="Zucchero a velo per decorare", unit="q.b.").model_dump(),
            ],
            "recipe_step": [
                "Preriscaldare il forno statico a 180°C. Imburrare e infarinare una tortiera da 22-24 cm di diametro.",
                "Separare i tuorli dagli albumi. Montare gli albumi a neve ben ferma con un pizzico di sale e tenere da parte.",
                "In un'altra ciotola capiente, lavorare i tuorli con lo zucchero usando le fruste elettriche, fino ad ottenere un composto chiaro e spumoso (circa 5-7 minuti).",
                "Aggiungere la scorza di limone grattugiata e il burro fuso intiepidito, continuando a mescolare.",
                "Setacciare insieme la farina, la fecola e il lievito. Incorporarli gradualmente al composto di tuorli, alternando con gli albumi montati a neve.",
                "Per incorporare gli albumi, procedere delicatamente con una spatola, con movimenti dal basso verso l'alto per non smontare il composto.",
                "Versare l'impasto omogeneo nella tortiera preparata e livellare la superficie.",
                "Cuocere in forno per circa 35-40 minuti. Fare la prova stecchino: se esce asciutto, la torta è pronta.",
                "Sfornare, lasciare intiepidire per 10 minuti nella tortiera, poi sformare su una gratella e far raffreddare completamente.",
                "Una volta fredda, cospargere con abbondante zucchero a velo."
            ],
            "description": "Una torta classica italiana, incredibilmente soffice e leggera, perfetta per la colazione o una merenda genuina. Il segreto sta nella lavorazione delle uova e nell'uso della fecola.", 
            "language": "italiano", "shortcode": "margherita_nonna_01", "diet": "Vegetariano", "cuisine_type": "Italiana",
            "tags": ["torta semplice", "colazione", "merenda", "soffice", "limone", "fecola"]
        },
        {
            "title": "Risotto ai Funghi Porcini Freschi", "category": ["Primi piatti", "Risotti", "Autunno"],
            "preparation_time": 20, "cooking_time": 45, # Include pulizia funghi e cottura brodo
            "ingredients": [
                Ingredient(name="Riso Carnaroli o Arborio", quantity="320", unit="g").model_dump(), 
                Ingredient(name="Funghi porcini freschi", quantity="400", unit="g").model_dump(),
                Ingredient(name="Brodo vegetale caldo", quantity="1.2", unit="litri circa").model_dump(), 
                Ingredient(name="Vino bianco secco", quantity="100", unit="ml").model_dump(),
                Ingredient(name="Scalogno o cipolla bianca piccola", quantity="1").model_dump(), 
                Ingredient(name="Burro freddo per mantecare", quantity="40", unit="g").model_dump(),
                Ingredient(name="Parmigiano Reggiano DOP grattugiato", quantity="60", unit="g").model_dump(), 
                Ingredient(name="Olio extravergine d'oliva", quantity="3", unit="cucchiai").model_dump(),
                Ingredient(name="Prezzemolo fresco tritato", quantity="2", unit="cucchiai").model_dump(), 
                Ingredient(name="Sale fino", unit="q.b.").model_dump(), 
                Ingredient(name="Pepe nero macinato fresco", unit="q.b.").model_dump(),
            ],
            "recipe_step": [
                "Pulire delicatamente i funghi porcini con un panno umido e un coltellino, eliminando la terra. Tagliarli a fettine o cubetti.",
                "Tritare finemente lo scalogno (o la cipolla).",
                "In una casseruola dai bordi alti (ideale per risotti), scaldare l'olio extravergine d'oliva. Aggiungere lo scalogno tritato e farlo appassire a fuoco dolce per qualche minuto.",
                "Alzare leggermente la fiamma, aggiungere i funghi porcini e farli saltare per 5-7 minuti, finché avranno rilasciato la loro acqua e inizieranno a dorare. Salare leggermente.",
                "Togliere circa un terzo dei funghi dalla casseruola e tenerli da parte per la decorazione finale.",
                "Aggiungere il riso nella casseruola con i funghi rimanenti e farlo tostare per 2-3 minuti, mescolando continuamente, finché i chicchi diventano traslucidi.",
                "Sfumare con il vino bianco e lasciare evaporare l'alcool.",
                "Iniziare ad aggiungere il brodo vegetale caldo, un mestolo alla volta, aspettando che il precedente sia assorbito prima di aggiungerne altro. Mescolare frequentemente.",
                "Continuare la cottura del risotto per circa 15-18 minuti (o secondo il tempo indicato sulla confezione del riso), aggiungendo brodo man mano. Il riso deve essere cotto al dente e il risotto cremoso all'onda.",
                "A cottura quasi ultimata, regolare di sale e pepe.",
                "Togliere la casseruola dal fuoco. Mantecare il risotto aggiungendo il burro freddo a pezzetti e il Parmigiano Reggiano grattugiato. Mescolare energicamente per creare una crema.",
                "Aggiungere il prezzemolo tritato e i funghi tenuti da parte. Coprire e lasciare riposare per 1-2 minuti.",
                "Servire immediatamente, decorando i piatti con altro prezzemolo fresco se gradito."
            ],
            "description": "Un classico intramontabile della cucina italiana, il risotto ai funghi porcini freschi è un piatto elegante e ricco di sapore, perfetto per celebrare i profumi dell'autunno.", 
            "language": "italiano", "shortcode": "risotto_porcini_01", "diet": "Vegetariano", "cuisine_type": "Italiana",
            "tags": ["risotto", "funghi porcini", "autunno", "primo piatto", "comfort food", "parmigiano"]
        }
    ]

    if force_populate and collection.count_documents({}) > 0 :
        print(f"Rimozione di {collection.count_documents({})} documenti esistenti dalla collezione '{collection.name}' prima del popolamento forzato...")
        collection.delete_many({})

    recipes_to_insert_validated = []
    for recipe_data in sample_recipes_raw_data:
        # Per l'embedding di esempio, combiniamo titolo, descrizione e ingredienti (nomi).
        # Questo può essere affinato per migliorare la pertinenza della ricerca.
        ingredient_names = ", ".join([ing['name'] for ing in recipe_data['ingredients']])
        text_to_embed = f"Titolo: {recipe_data['title']}. Descrizione: {recipe_data['description']}. Ingredienti: {ingredient_names}"
        
        embedding_vector = chatbot.get_embedding(text_to_embed)
        
        # Aggiungi il campo embedding al dizionario della ricetta
        recipe_data_with_embedding = {**recipe_data, "embedding": embedding_vector}
        
        # Validazione con Pydantic prima dell'inserimento
        try:
            # Converti lista di dict di ingredienti in lista di oggetti Ingredient per la validazione
            # Questo passaggio è già stato fatto sopra creando i dict con .model_dump()
            validated_recipe = RecipeDBSchema(**recipe_data_with_embedding)
            recipes_to_insert_validated.append(validated_recipe.model_dump()) # Usa model_dump per ottenere un dict
        except ValidationError as e:
            print(f"Errore di validazione Pydantic per la ricetta '{recipe_data.get('title', 'N/D')}':")
            print(e.errors())
            continue # Salta questa ricetta se non è valida

    if recipes_to_insert_validated:
        try:
            collection.insert_many(recipes_to_insert_validated)
            print(f"Inseriti {len(recipes_to_insert_validated)} documenti di esempio nella collezione '{collection.name}'.")
            print("\n--- IMPORTANTE: CONFIGURAZIONE INDICE VETTORIALE ATLAS ---")
            print(f"Assicurati di aver creato un indice di tipo 'vectorSearch' (Atlas Vector Search) su MongoDB Atlas per la collezione '{collection.name}'.")
            print(f"L'indice deve essere configurato per il campo 'embedding' e avere {chatbot.embedding_dim} dimensioni.")
            print("Ecco un esempio della definizione JSON dell'indice da creare in Atlas (tramite UI o mongosh):")
            print(f"""
            {{
              "name": "{chatbot.vector_index_name}",  // Puoi scegliere un nome, ma DEVE corrispondere a quello usato nel codice
              "type": "vectorSearch",
              "definition": {{
                "fields": [
                  {{
                    "type": "vector",
                    "path": "embedding",         // Il campo che contiene i vettori
                    "numDimensions": {chatbot.embedding_dim},    // La dimensione degli embedding del tuo modello
                    "similarity": "cosine"       // O "euclidean" o "dotProduct" a seconda delle tue esigenze
                  }}
                  // Puoi aggiungere altri campi per il pre-filtering se necessario, ad es.
                  // {{
                  //   "type": "filter",
                  //   "path": "category" 
                  // }},
                  // {{
                  //   "type": "filter",
                  //   "path": "language"
                  // }}
                ]
              }}
            }}
            """)
            print("-----------------------------------------------------------\n")
        except Exception as e:
            print(f"Errore durante l'inserimento dei dati di esempio: {e}")
    else:
        print("Nessun dato di esempio valido da popolare (potrebbero esserci stati errori di validazione).")

# 4. Loop principale di interazione
if __name__ == "__main__":
    print("--- Chatbot di Ricette MVP con MongoDB Atlas Vector Search ---")
    print("Questo script è un Minimum Viable Product (MVP).")
    print("Assicurati che il tuo cluster Atlas sia attivo, l'IP sia autorizzato,")
    print("e la stringa di connessione (MONGO_URI) sia configurata correttamente.")
    print("Verifica anche che l'indice vettoriale sia stato creato sulla collezione come indicato.\n")

    # --- CONFIGURAZIONE OBBLIGATORIA ---
    # Sostituire con i propri valori! È VIVAMENTE consigliato usare variabili d'ambiente.
    # Esempio: MONGO_URI = os.getenv("MONGO_ATLAS_URI", "mongodb+srv://<UTENTE>:<PASSWORD>@<NOME_CLUSTER>.<ID_CLUSTER>.mongodb.net/?retryWrites=true&w=majority")
    
    # Inserisci qui la tua stringa di connessione MongoDB Atlas
    # Esempio: "mongodb+srv://mioUtente:miaPassword@mioCluster.xxxx.mongodb.net/?retryWrites=true&w=majority"
    MONGO_URI = "mongodb+srv://<UTENTE>:<PASSWORD>@<NOME_CLUSTER>.<ID_CLUSTER>.mongodb.net/" 
    
    DB_NAME = "db_ricette_chatbot"       # Puoi scegliere un nome per il tuo database
    COLLECTION_NAME = "ricette_vettoriali" # Puoi scegliere un nome per la tua collezione
    
    # Nome dell'indice vettoriale che hai creato/creerai su Atlas.
    # Deve corrispondere ESATTAMENTE a quello definito nella UI di Atlas o tramite mongosh.
    VECTOR_SEARCH_INDEX_NAME = "idx_ricette_embedding_cosine" # Esempio di nome indice

    # Controllo di base sulla configurazione di MONGO_URI
    if "<UTENTE>" in MONGO_URI or "<PASSWORD>" in MONGO_URI or "<NOME_CLUSTER>" in MONGO_URI:
        print("*********************************************************************************")
        print("ATTENZIONE: La stringa di connessione MONGO_URI non sembra essere configurata!")
        print("Modifica il file main_chatbot.py (o imposta la variabile d'ambiente) con i tuoi dati di accesso a MongoDB Atlas.")
        print("Lo script non funzionerà correttamente senza una connessione valida.")
        print("*********************************************************************************")
        # Potresti voler uscire qui, ma per permettere test di parti del codice, continuiamo con cautela.
        # exit(1) 

    try:
        recipe_chatbot = RecipeChatbot(
            mongo_uri=MONGO_URI,
            db_name=DB_NAME,
            collection_name=COLLECTION_NAME,
            vector_index_name=VECTOR_SEARCH_INDEX_NAME
        )

        # Chiedi se popolare i dati solo se la collezione è vuota o se si vuole forzare
        if recipe_chatbot.collection.count_documents({}) == 0:
            choice = input(f"La collezione '{COLLECTION_NAME}' è vuota. Vuoi popolarla con alcuni dati di esempio? (s/n): ").strip().lower()
            if choice == 's':
                populate_sample_data(recipe_chatbot, force_populate=True)
        else:
            print(f"Trovati {recipe_chatbot.collection.count_documents({})} documenti nella collezione '{COLLECTION_NAME}'.")
            choice_repopulate = input("Vuoi ri-popolare i dati di esempio? (ATTENZIONE: questo cancellerà i dati esistenti nella collezione) (s/n): ").strip().lower()
            if choice_repopulate == 's':
                 populate_sample_data(recipe_chatbot, force_populate=True)


        print("\nCiao! Sono il tuo assistente culinario virtuale.")
        print("Posso aiutarti a trovare ricette. Chiedimi pure!")
        print("Ad esempio: 'Come si fa la carbonara?', 'idee per un dolce al cioccolato', 'ricetta vegetariana veloce'")
        print("Scrivi 'esci' per terminare la conversazione.")
        
        while True:
            user_input = input("Tu: ").strip()
            if user_input.lower() == 'esci':
                break
            if not user_input: # Ignora input vuoti
                continue
            
            response = recipe_chatbot.ask(user_input)
            print(f"Chatbot: {response}")

    except Exception as e: # Cattura eccezioni generiche che potrebbero non essere state gestite prima
        print(f"Si è verificato un errore critico non gestito nell'applicazione: {e}")
        print(f"Tipo di errore: {type(e).__name__}")
        print("Controlla la configurazione, la connessione a MongoDB Atlas, l'indice vettoriale e i log precedenti per dettagli.")

    print("\nGrazie per aver utilizzato il Chatbot di Ricette. Alla prossima!")
