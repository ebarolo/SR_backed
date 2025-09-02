
import asyncio
from typing import List
from DB.langchain import get_langchain_recipe_db
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from models import RecipeDBSchema, Ingredient
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_recipes() -> List[RecipeDBSchema]:
    """Crea alcune ricette di esempio"""
    
    recipes = [
        RecipeDBSchema(
            title="Pasta all'Amatriciana",
            category=["Primi Piatti", "Tradizionale"],
            preparation_time=10,
            cooking_time=20,
            ingredients=[
                Ingredient(name="spaghetti", qt=400, um="g"),
                Ingredient(name="guanciale", qt=150, um="g"),
                Ingredient(name="pomodori pelati", qt=400, um="g"),
                Ingredient(name="pecorino romano", qt=100, um="g"),
                Ingredient(name="vino bianco", qt=50, um="ml"),
                Ingredient(name="sale", qt=1, um="qb"),
                Ingredient(name="pepe nero", qt=1, um="qb")
            ],
            recipe_step=[
                "Tagliare il guanciale a listarelle",
                "Rosolare il guanciale in padella senza olio",
                "Sfumare con vino bianco",
                "Aggiungere i pomodori pelati schiacciati",
                "Cuocere per 10 minuti",
                "Nel frattempo cuocere la pasta al dente",
                "Scolare la pasta e saltarla nel sugo",
                "Servire con abbondante pecorino e pepe"
            ],
            description="La vera ricetta romana dell'Amatriciana, con guanciale croccante e pecorino",
            diet="normale",
            technique="rosolatura",
            language="it",
            chef_advise="Usa guanciale di qualità e non pancetta. Il pecorino deve essere romano DOP",
            tags=["pasta", "romano", "tradizionale", "guanciale"],
            nutritional_info=["Calorie: 550 per porzione", "Proteine: 20g", "Carboidrati: 70g"],
            cuisine_type="italiana",
            ricetta_audio=None,
            ricetta_caption="Piatto di pasta con sugo rosso e guanciale dorato",
            shortcode="PASTA_AMATRICIANA_001"
        ),
        
        RecipeDBSchema(
            title="Risotto ai Funghi Porcini",
            category=["Primi Piatti", "Vegetariano"],
            preparation_time=20,
            cooking_time=25,
            ingredients=[
                Ingredient(name="riso carnaroli", qt=320, um="g"),
                Ingredient(name="funghi porcini freschi", qt=300, um="g"),
                Ingredient(name="funghi porcini secchi", qt=30, um="g"),
                Ingredient(name="cipolla", qt=1, um="pz"),
                Ingredient(name="vino bianco", qt=100, um="ml"),
                Ingredient(name="brodo vegetale", qt=1.5, um="l"),
                Ingredient(name="burro", qt=50, um="g"),
                Ingredient(name="parmigiano", qt=80, um="g"),
                Ingredient(name="prezzemolo", qt=1, um="mazzetto")
            ],
            recipe_step=[
                "Ammollare i funghi secchi in acqua tiepida",
                "Pulire e tagliare i funghi freschi",
                "Tritare finemente la cipolla",
                "Tostare il riso in padella",
                "Sfumare con vino bianco",
                "Aggiungere il brodo un mestolo alla volta",
                "A metà cottura aggiungere i funghi",
                "Mantecare con burro e parmigiano",
                "Servire con prezzemolo tritato"
            ],
            description="Cremoso risotto mantecato con funghi porcini freschi e secchi",
            diet="vegetariano",
            technique="mantecatura",
            language="it",
            chef_advise="Non mescolare troppo il risotto, basta scuotere la padella. Il riso deve rimanere all'onda",
            tags=["risotto", "funghi", "autunno", "vegetariano"],
            nutritional_info=["Calorie: 420 per porzione", "Proteine: 12g", "Carboidrati: 65g"],
            cuisine_type="italiana",
            ricetta_audio=None,
            ricetta_caption="Risotto cremoso con funghi porcini e prezzemolo",
            shortcode="RISOTTO_FUNGHI_001"
        ),
        
        RecipeDBSchema(
            title="Tiramisù Classico",
            category=["Dolci", "Senza Cottura"],
            preparation_time=30,
            cooking_time=0,
            ingredients=[
                Ingredient(name="mascarpone", qt=500, um="g"),
                Ingredient(name="savoiardi", qt=300, um="g"),
                Ingredient(name="uova", qt=4, um="pz"),
                Ingredient(name="zucchero", qt=100, um="g"),
                Ingredient(name="caffè espresso", qt=300, um="ml"),
                Ingredient(name="cacao amaro", qt=30, um="g"),
                Ingredient(name="liquore al caffè", qt=50, um="ml")
            ],
            recipe_step=[
                "Preparare il caffè e lasciarlo raffreddare",
                "Separare tuorli e albumi",
                "Montare i tuorli con lo zucchero",
                "Aggiungere il mascarpone ai tuorli",
                "Montare gli albumi a neve",
                "Incorporare delicatamente gli albumi",
                "Bagnare i savoiardi nel caffè",
                "Alternare strati di crema e savoiardi",
                "Spolverare con cacao amaro",
                "Refrigerare per almeno 4 ore"
            ],
            description="Il dolce italiano più amato al mondo, cremoso e al caffè",
            diet="vegetariano",
            technique="montatura",
            language="it",
            chef_advise="Usa uova freschissime e mascarpone di qualità. Non bagnare troppo i savoiardi",
            tags=["dolce", "caffè", "mascarpone", "senza-cottura"],
            nutritional_info=["Calorie: 380 per porzione", "Proteine: 8g", "Carboidrati: 35g"],
            cuisine_type="italiana",
            ricetta_audio=None,
            ricetta_caption="Tiramisù con strati di savoiardi e crema al mascarpone, spolverato di cacao",
            shortcode="TIRAMISU_CLASSICO_001"
        )
    ]
    
    return recipes


async def example_usage():
    """Esempio completo di utilizzo del sistema Langchain"""
    
    # 1. Inizializza il database
    logger.info("Inizializzazione database Langchain...")
    db = get_langchain_recipe_db()
    
    # 2. Mostra statistiche iniziali
    stats = db.get_statistics()
    logger.info(f"Statistiche iniziali: {stats}")
    
    # 3. Aggiungi ricette di esempio
    logger.info("\n--- AGGIUNTA RICETTE ---")
    recipes = create_sample_recipes()
    
    # Aggiungi singola ricetta
    success = db.add_recipe(recipes[0])
    logger.info(f"Aggiunta prima ricetta: {'Successo' if success else 'Fallito'}")
    
    # Aggiungi ricette in batch
    success_count, errors = db.add_recipes_batch(recipes[1:])
    logger.info(f"Aggiunte {success_count} ricette in batch. Errori: {errors}")
    
    # 4. Ricerca semantica
    logger.info("\n--- RICERCA SEMANTICA ---")
    
    # Ricerca semplice
    query = "ricetta con funghi per l'autunno"
    results = db.search_similar(query, k=5)
    logger.info(f"\nRicerca: '{query}'")
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. {result['title']} (score: {result['score']:.3f})")
    
    # Ricerca con filtri
    query = "primo piatto veloce"
    filters = {"max_time": 30}  # Max 30 minuti totali
    results = db.search_similar(query, k=5, filter_dict=filters)
    logger.info(f"\nRicerca con filtri: '{query}' (max 30 min)")
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. {result['title']} - Tempo totale: {result['total_time']} min")
    
    # 5. Domande con LLM
    logger.info("\n--- DOMANDE CON LLM ---")
    
    questions = [
        "Quali ricette posso preparare se sono vegetariano?",
        "Come si prepara un buon risotto? Quali sono i segreti?",
        "Ho del guanciale e dei pomodori, cosa posso cucinare?",
        "Qual è la differenza tra i tempi di preparazione dei primi piatti?"
    ]
    
    for question in questions:
        logger.info(f"\nDomanda: {question}")
        answer = db.ask_about_recipes(question)
        logger.info(f"Risposta: {answer}")

    # 5b. Dimostrazione stile LCEL RAG esplicito
    logger.info("\n--- LCEL RAG ESPlicito (Demo) ---")
    retriever = db.vectorstore.as_retriever(search_kwargs={"k": 4})
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Sei un assistente culinario. Rispondi in italiano, breve e preciso.\nContesto:\n{context}"),
        ("human", "Domanda: {input}")
    ])
    combine_docs = create_stuff_documents_chain(db.llm, prompt)
    rag = create_retrieval_chain(retriever, combine_docs)

    demo_question = "Consigli per un risotto ben mantecato?"
    demo_result = rag.invoke({"input": demo_question})
    logger.info(f"Domanda (LCEL): {demo_question}")
    logger.info(f"Risposta (LCEL): {demo_result.get('answer')}")
    
    # 6. Recupero ricetta specifica
    logger.info("\n--- RECUPERO RICETTA SPECIFICA ---")
    recipe = db.get_recipe_by_shortcode("TIRAMISU_CLASSICO_001")
    if recipe:
        logger.info(f"Trovata ricetta: {recipe['title']}")
        logger.info(f"Ingredienti: {recipe['ingredients_list']}")
    
    # 7. Esporta metadati
    logger.info("\n--- ESPORTAZIONE METADATI ---")
    all_metadata = db.export_recipes_metadata()
    logger.info(f"Esportate {len(all_metadata)} ricette")
    
    # 8. Statistiche finali
    final_stats = db.get_statistics()
    logger.info(f"\nStatistiche finali: {final_stats}")


def example_migration():
    """Esempio di migrazione dal sistema ChromaDB esistente"""
    logger.info("\n--- MIGRAZIONE DA CHROMADB ESISTENTE ---")
    
    from DB.langchain import migrate_from_chromadb
    
    # Esegui migrazione
    migrated, errors = migrate_from_chromadb()
    
    logger.info(f"Migrate {migrated} ricette")
    if errors:
        logger.warning(f"Errori durante la migrazione: {errors[:5]}")  # Mostra primi 5 errori


if __name__ == "__main__":
    # Esegui esempio principale
    asyncio.run(example_usage())
    
    # Opzionale: esegui migrazione
    # example_migration()
