from typing import List, Dict, Any, Optional, Tuple
import uuid
import logging
from datetime import datetime

# Langchain imports
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_openai import ChatOpenAI

# Imports locali
from config import OPENAI_API_KEY, CHROMA_LOCAL_PATH, COLLECTION_NAME, OPENAI_RESPONSES_MODEL
from models import RecipeDBSchema
from logging_config import get_error_logger
from utility import nfkc, lemmatize_it, remove_stopwords_spacy

# Logger
logger = logging.getLogger(__name__)
error_logger = get_error_logger(__name__)


class LangchainRecipeDB:
    """
    Gestione database ricette con Langchain, OpenAI embeddings e ChromaDB
    
    Questa classe fornisce:
    - Generazione di embeddings con modello OpenAI text-embedding-3-large
    - Memorizzazione persistente in ChromaDB
    - Ricerca semantica avanzata
    - Filtraggio per metadati
    - Chain di retrieval con LLM per risposte contestuali
    """
    
    def __init__(self, 
                 openai_api_key: str = OPENAI_API_KEY,
                 persist_directory: str = CHROMA_LOCAL_PATH,
                 collection_name: str = COLLECTION_NAME):
        """
        Inizializza il database Langchain per le ricette
        
        Args:
            openai_api_key: API key per OpenAI
            persist_directory: Directory per persistenza ChromaDB
            collection_name: Nome della collection
        """
        self.openai_api_key = openai_api_key
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Inizializza embeddings con modello large di OpenAI
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.openai_api_key,
            model="text-embedding-3-large",  # Modello più potente per migliori risultati
            dimensions=3072  # Dimensioni del modello large
        )
        
        # Inizializza text splitter per documenti lunghi
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )
        
        # Inizializza o carica il vector store
        self._initialize_vectorstore()
        
        # Inizializza LLM per chain di retrieval (modelli aggiornati)
        # Usa il valore da config se valido, altrimenti fallback sicuro
        def _resolve_model_name(name: Optional[str]) -> str:
            try:
                if not name:
                    return "gpt-4o-mini"
                n = str(name).strip().lower()
                # Evita placeholder/nomi non validi
                if n.startswith(" ") or n in {"", "none", "null"}:
                    return "gpt-4o-mini"
                return name
            except Exception:
                return "gpt-4o-mini"

        self.llm = ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model=_resolve_model_name(OPENAI_RESPONSES_MODEL),
            temperature=0.3
        )
        
        # Statistiche
        self.stats = {
            "total_recipes": 0,
            "last_update": None
        }
    
    def _initialize_vectorstore(self):
        """Inizializza o carica il vector store ChromaDB"""
        try:
            # Carica/crea vector store (solo API pubbliche)
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            
            logger.info("Vector store inizializzato")
        except Exception as e:
            logger.warning(f"Creazione nuovo vector store: {str(e)}")
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        # Contatore documenti mantenuto a livello applicativo (no API private)
        self._doc_count: Optional[int] = 0
    
    def _recipe_to_documents(self, recipe: RecipeDBSchema) -> List[Document]:
        """
        Converte una ricetta in documenti Langchain
        
        Args:
            recipe: Schema della ricetta
            
        Returns:
            Lista di documenti Langchain
        """
        # Processa ingredienti
        ingredients_processed = []
        for ingredient in recipe.ingredients:
            name_normalized = nfkc(ingredient.name)
            name_cleaned = remove_stopwords_spacy(name_normalized)
            #name_lemmatized = lemmatize_it(name_cleaned)
            ingredients_processed.append(f"{name_cleaned})")
        
        # Crea testo principale della ricetta
        recipe_text = f"""
Titolo: {recipe.title}

Descrizione: {recipe.description}

Categoria: {', '.join(recipe.category)}
Tipo di Cucina: {recipe.cuisine_type or ''}

Ingredienti:
{chr(10).join(f"- {ing}" for ing in ingredients_processed)}

"""        
        # Crea metadati strutturati
        metadata = {
            "shortcode": recipe.shortcode,
            "title": recipe.title,
            "category": ', '.join(recipe.category),
            "cuisine_type": recipe.cuisine_type or "",
            "diet": recipe.diet or "",
            "technique": recipe.technique or "",
            "cooking_time": recipe.cooking_time or 0,
            "preparation_time": recipe.preparation_time or 0,
            "total_time": (recipe.cooking_time or 0) + (recipe.preparation_time or 0),
            "ingredients_count": len(recipe.ingredients),
            "ingredients_list": ', '.join([ing.name for ing in recipe.ingredients]),
            "language": recipe.language
        }
        
        # Dividi il testo se troppo lungo
        text_chunks = self.text_splitter.split_text(recipe_text)
        
        # Crea documenti
        documents = []
        for i, chunk in enumerate(text_chunks):
            doc_metadata = metadata.copy()
            doc_metadata["chunk_index"] = i
            doc_metadata["total_chunks"] = len(text_chunks)
            
            doc = Document(
                page_content=chunk,
                metadata=doc_metadata
            )
            documents.append(doc)
        
        return documents
    
    def add_recipe(self, recipe: RecipeDBSchema) -> bool:
        """
        Aggiunge una ricetta al database con embedding OpenAI
        
        Args:
            recipe: Ricetta da aggiungere
            
        Returns:
            True se successo, False altrimenti
        """
        try:
            # Converti ricetta in documenti
            documents = self._recipe_to_documents(recipe)
            
            # Aggiungi al vector store
            self.vectorstore.add_documents(
                documents=documents,
                ids=[f"{recipe.shortcode}_chunk_{i}" for i in range(len(documents))]
            )

            # Aggiorna statistiche
            self.stats["total_recipes"] += 1
            self.stats["last_update"] = datetime.now()
            try:
                self._doc_count = (self._doc_count or 0) + len(documents)
            except Exception:
                pass
            
            logger.info(f"Ricetta {recipe.shortcode} aggiunta con {len(documents)} chunks")
            return True
            
        except Exception as e:
            error_logger.log_exception("add_recipe", e, {
                "shortcode": recipe.shortcode,
                "title": recipe.title
            })
            return False
    
    def add_recipes_batch(self, recipes: List[RecipeDBSchema]) -> Tuple[int, List[str]]:
        """
        Aggiunge multiple ricette in batch per efficienza
        
        Args:
            recipes: Lista di ricette da aggiungere
            
        Returns:
            Tupla (numero_successi, lista_errori)
        """
        success_count = 0
        errors = []
        all_documents = []
        all_ids = []
        
        for recipe in recipes:
            try:
                documents = self._recipe_to_documents(recipe)
                all_documents.extend(documents)
                all_ids.extend([f"{recipe.shortcode}_chunk_{i}" for i in range(len(documents))])
                success_count += 1
            except Exception as e:
                errors.append(f"{recipe.shortcode}: {str(e)}")
        
        if all_documents:
            try:
                # Aggiungi tutti i documenti in una volta
                self.vectorstore.add_documents(
                    documents=all_documents,
                    ids=all_ids
                )
                self.vectorstore.persist()
                
                # Aggiorna statistiche
                self.stats["total_recipes"] += success_count
                self.stats["last_update"] = datetime.now()
                try:
                    self._doc_count = (self._doc_count or 0) + len(all_documents)
                except Exception:
                    pass
                
            except Exception as e:
                error_logger.log_exception("add_recipes_batch", e)
                return 0, [str(e)]
        
        return success_count, errors
    
    def search_similar(self, 
                      query: str, 
                      k: int = 10,
                      filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Ricerca semantica per ricette simili
        
        Args:
            query: Query di ricerca
            k: Numero di risultati
            filter_dict: Filtri sui metadati (es. {"cuisine_type": "italiana"})
            
        Returns:
            Lista di ricette con score di similarità
        """
        try:
            # Costruisci filtro per ChromaDB
            where_clause = None
            if filter_dict:
                where_clause = {}
                for key, value in filter_dict.items():
                    if key == "max_time":
                        where_clause["total_time"] = {"$lte": value}
                    elif key == "min_time":
                        where_clause["total_time"] = {"$gte": value}
                    elif key == "category":
                        where_clause["category"] = {"$contains": value}
                    elif key == "diet":
                        where_clause["diet"] = {"$eq": value}
                    elif key == "cuisine_type":
                        where_clause["cuisine_type"] = {"$eq": value}
                    else:
                        where_clause[key] = {"$eq": value}
            
            # Esegui ricerca
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k * 2,  # Prendiamo più risultati per poi deduplicare
                filter=where_clause
            )
            
            # Deduplica per shortcode e prendi il miglior score
            seen_shortcodes = {}
            for doc, score in results:
                shortcode = doc.metadata["shortcode"]
                if shortcode not in seen_shortcodes or score < seen_shortcodes[shortcode]["score"]:
                    seen_shortcodes[shortcode] = {
                        "shortcode": shortcode,
                        "title": doc.metadata["title"],
                        "category": doc.metadata["category"].split(", ") if doc.metadata["category"] else [],
                        "cuisine_type": doc.metadata["cuisine_type"],
                        "diet": doc.metadata["diet"],
                        "cooking_time": doc.metadata["cooking_time"],
                        "preparation_time": doc.metadata["preparation_time"],
                        "total_time": doc.metadata["total_time"],
                        "score": float(score),
                        "content_preview": doc.page_content[:200] + "..."
                    }
            
            # Ordina per score e prendi i top k
            final_results = sorted(
                seen_shortcodes.values(), 
                key=lambda x: x["score"]
            )[:k]
            
            return final_results
            
        except Exception as e:
            error_logger.log_exception("search_similar", e, {
                "query": query[:50],
                "k": k,
                "filter_dict": filter_dict
            })
            return []
    
    def ask_about_recipes(self,
                         question: str,
                         k: int = 5) -> str:
        """
        Risponde a domande sulle ricette usando la nuova API LangChain (LCEL).

        Implementazione aggiornata con create_retrieval_chain e prompt strutturato.

        Args:
            question: Domanda in linguaggio naturale
            k: Numero di documenti da recuperare

        Returns:
            Risposta generata dal LLM
        """
        try:
            # Retriever dal vectorstore
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})

            # Prompt in stile Chat con variabili {context} e {input}
            prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "Sei un assistente culinario. Rispondi in italiano in modo conciso e pratico. "
                    "Usa esclusivamente il contesto fornito. Se l'informazione non è nel contesto, di' che non lo sai.\n"
                    "Contesto:\n{context}"
                ),
                ("human", "Domanda: {input}")
            ])

            # Chain di stuffing dei documenti e chain di retrieval
            combine_docs_chain = create_stuff_documents_chain(self.llm, prompt)
            rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

            # Invoca la chain con l'input dell'utente
            result = rag_chain.invoke({"input": question})

            # Estrai risposta e ricette citate (se disponibili)
            answer = result.get("answer") or ""
            cited_recipes = set()
            for doc in result.get("context", []) or []:
                try:
                    title = doc.metadata.get("title")
                    if title:
                        cited_recipes.add(title)
                except Exception:
                    continue

            if cited_recipes:
                answer += f"\n\nRicette consultate: {', '.join(sorted(cited_recipes))}"

            return answer.strip() or "Mi dispiace, non ho trovato informazioni rilevanti nel contesto disponibile."

        except Exception as e:
            error_logger.log_exception("ask_about_recipes", e, {"question": question[:50]})
            return "Mi dispiace, si è verificato un errore nell'elaborazione della domanda."
    
    def get_recipe_by_shortcode(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """
        Recupera una ricetta specifica per shortcode
        
        Args:
            shortcode: Codice univoco della ricetta
            
        Returns:
            Dati della ricetta o None
        """
        try:
            # Cerca documenti con questo shortcode
            results = self.vectorstore.similarity_search(
                query="",  # Query vuota
                k=10,
                filter={"shortcode": shortcode}
            )
            
            if not results:
                return None
            
            # Prendi il primo documento (dovrebbero essere tutti della stessa ricetta)
            doc = results[0]
            metadata = doc.metadata
            
            return {
                "shortcode": shortcode,
                "title": metadata["title"],
                "category": metadata["category"].split(", ") if metadata["category"] else [],
                "cuisine_type": metadata["cuisine_type"],
                "diet": metadata["diet"],
                "cooking_time": metadata["cooking_time"],
                "preparation_time": metadata["preparation_time"],
                "technique": metadata.get("technique", ""),
                "ingredients_list": metadata.get("ingredients_list", ""),
                "content": doc.page_content
            }
            
        except Exception as e:
            error_logger.log_exception("get_recipe_by_shortcode", e, {"shortcode": shortcode})
            return None
    
    def delete_recipe(self, shortcode: str) -> bool:
        """
        Elimina una ricetta dal database
        
        Args:
            shortcode: Codice della ricetta da eliminare
            
        Returns:
            True se eliminata, False altrimenti
        """
        try:
            # Conta quanti chunk esistono per questa ricetta usando API pubbliche
            try:
                existing_docs = self.vectorstore.similarity_search(
                    query=".",
                    k=1000,
                    filter={"shortcode": shortcode}
                )
                chunk_count = len(existing_docs)
            except Exception:
                chunk_count = 0

            # Eliminazione tramite API pubblica del vectorstore (where filter)
            self.vectorstore.delete(where={"shortcode": shortcode})

            # Aggiorna statistiche applicative
            self.stats["total_recipes"] = max(0, self.stats.get("total_recipes", 0) - 1)
            self.stats["last_update"] = datetime.now()
            try:
                if self._doc_count is not None:
                    self._doc_count = max(0, self._doc_count - chunk_count)
            except Exception:
                pass

            logger.info(f"Ricetta {shortcode} eliminata")
            return True

        except Exception as e:
            error_logger.log_exception("delete_recipe", e, {"shortcode": shortcode})
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Ottiene statistiche del database
        
        Returns:
            Dizionario con statistiche
        """
        try:
            # Usa solo API pubbliche: conteggio mantenuto a livello app
            total_docs = self._doc_count
            # Stima ricette uniche: se non noto, usa contatore ricette
            estimated_recipes = max(self.stats.get("total_recipes", 0), (total_docs or 0) // 2)

            return {
                "total_documents": total_docs,
                "estimated_recipes": estimated_recipes,
                "collection_name": self.collection_name,
                "embedding_model": "text-embedding-3-large",
                "embedding_dimensions": 3072,
                "last_update": self.stats.get("last_update"),
                "status": "active"
            }

        except Exception as e:
            error_logger.log_exception("get_statistics", e)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def export_recipes_metadata(self) -> List[Dict[str, Any]]:
        """
        Esporta tutti i metadati delle ricette
        
        Returns:
            Lista di metadati delle ricette
        """
        try:
            collection = self.vectorstore._collection
            
            # Ottieni tutti i documenti
            all_docs = collection.get()
            
            # Deduplica per shortcode
            recipes_map = {}
            for i, metadata in enumerate(all_docs["metadatas"]):
                shortcode = metadata["shortcode"]
                if shortcode not in recipes_map:
                    recipes_map[shortcode] = metadata
            
            return list(recipes_map.values())
            
        except Exception as e:
            error_logger.log_exception("export_recipes_metadata", e)
            return []


# Istanza singleton per compatibilità
langchain_recipe_db = None

def get_langchain_recipe_db() -> LangchainRecipeDB:
    """
    Ottiene l'istanza singleton del database Langchain
    
    Returns:
        Istanza di LangchainRecipeDB
    """
    global langchain_recipe_db
    if langchain_recipe_db is None:
        langchain_recipe_db = LangchainRecipeDB()
    return langchain_recipe_db


# Funzioni di utilità per migrazione da sistema esistente
def migrate_from_chromadb(source_collection_name: str = "smartRecipe") -> Tuple[int, List[str]]:
    """
    Migra ricette dal ChromaDB esistente al sistema Langchain
    
    Args:
        source_collection_name: Nome collection sorgente
        
    Returns:
        Tupla (numero_migrate, lista_errori)
    """
    try:
        import chromadb
        from DB.supbase import get_recipe_by_shortcode_supabase
        
        # Connetti al ChromaDB esistente
        client = chromadb.PersistentClient(path=CHROMA_LOCAL_PATH)
        source_collection = client.get_collection(name=source_collection_name)
        
        # Ottieni tutti i documenti
        all_docs = source_collection.get()
        
        # Estrai shortcodes unici
        shortcodes = set()
        for doc_id in all_docs["ids"]:
            shortcode = doc_id.split("_")[0]  # Assumendo formato "shortcode_chunk_n"
            shortcodes.add(shortcode)
        
        # Carica ricette complete da Supabase
        db = get_langchain_recipe_db()
        migrated = 0
        errors = []
        
        for shortcode in shortcodes:
            try:
                # Recupera ricetta completa
                recipe_data = get_recipe_by_shortcode_supabase(shortcode)
                if recipe_data:
                    recipe = RecipeDBSchema(**recipe_data)
                    if db.add_recipe(recipe):
                        migrated += 1
                    else:
                        errors.append(f"{shortcode}: Errore aggiunta")
                else:
                    errors.append(f"{shortcode}: Non trovata in Supabase")
                    
            except Exception as e:
                errors.append(f"{shortcode}: {str(e)}")
        
        return migrated, errors
        
    except Exception as e:
        return 0, [f"Errore migrazione: {str(e)}"]
