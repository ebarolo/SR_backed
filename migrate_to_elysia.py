#!/usr/bin/env python3
"""
Script di migrazione da ChromaDB a Elysia/Weaviate

Questo script permette di migrare le ricette esistenti da ChromaDB 
al nuovo sistema Elysia/Weaviate mantenendo tutti i metadati.

Utilizzo:
    python migrate_to_elysia.py [--dry-run] [--batch-size N]

Opzioni:
    --dry-run      Esegue una simulazione senza effettuare modifiche
    --batch-size   Numero di ricette da processare per batch (default: 10)
"""

import argparse
import json
import os
import sys
from typing import List, Optional
import logging

# Setup dei path per import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BASE_FOLDER_RICETTE, COLLECTION_NAME, ELYSIA_COLLECTION_NAME
from models import RecipeDBSchema
from DB.elysia import elysia_recipe_db, ingest_json_to_elysia
from DB.chromaDB import recipe_db as chroma_recipe_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_recipes_from_disk() -> List[RecipeDBSchema]:
    """
    Carica tutte le ricette dai file JSON sul disco
    
    Returns:
        Lista di ricette caricate
    """
    recipes = []
    
    if not os.path.exists(BASE_FOLDER_RICETTE):
        logger.error(f"Directory ricette non trovata: {BASE_FOLDER_RICETTE}")
        return recipes
    
    for entry in os.listdir(BASE_FOLDER_RICETTE):
        entry_path = os.path.join(BASE_FOLDER_RICETTE, entry)
        
        if not os.path.isdir(entry_path):
            continue
            
        json_file = os.path.join(entry_path, "media_original", f"metadata_{entry}.json")
        
        if not os.path.isfile(json_file):
            logger.warning(f"File metadata non trovato: {json_file}")
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                recipe_data_dict = json.load(f)
                
            recipe = RecipeDBSchema(**recipe_data_dict)
            recipes.append(recipe)
            logger.info(f"Caricata ricetta: {recipe.shortcode}")
            
        except Exception as e:
            logger.error(f"Errore caricamento ricetta da {json_file}: {e}")
            
    return recipes

def migrate_recipes_to_elysia(recipes: List[RecipeDBSchema], dry_run: bool = False, batch_size: int = 10) -> dict:
    """
    Migra le ricette a Elysia/Weaviate
    
    Args:
        recipes: Lista di ricette da migrare
        dry_run: Se True, simula senza effettuare modifiche
        batch_size: Numero di ricette per batch
        
    Returns:
        Statistiche della migrazione
    """
    total_recipes = len(recipes)
    migrated = 0
    errors = []
    
    logger.info(f"Inizio migrazione di {total_recipes} ricette a Elysia")
    
    if dry_run:
        logger.info("MODALITÀ DRY-RUN: nessuna modifica sarà effettuata")
    
    # Verifica connessione Elysia
    if not dry_run:
        if not elysia_recipe_db.collection:
            logger.error("Impossibile connettersi a Elysia/Weaviate")
            return {"migrated": 0, "errors": ["Connessione Elysia fallita"], "total": total_recipes}
    
    # Migrazione a batch
    for i in range(0, total_recipes, batch_size):
        batch = recipes[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_recipes + batch_size - 1) // batch_size
        
        logger.info(f"Processando batch {batch_num}/{total_batches} ({len(batch)} ricette)")
        
        if dry_run:
            # Simula il successo
            migrated += len(batch)
            for recipe in batch:
                logger.info(f"[DRY-RUN] Migrando ricetta: {recipe.shortcode}")
        else:
            # Migrazione reale
            try:
                success_count, batch_collection = ingest_json_to_elysia(batch, ELYSIA_COLLECTION_NAME)
                migrated += success_count
                
                if success_count != len(batch):
                    failed_count = len(batch) - success_count
                    errors.append(f"Batch {batch_num}: {failed_count} ricette fallite")
                    
                logger.info(f"Batch {batch_num}: {success_count}/{len(batch)} ricette migrate")
                
            except Exception as e:
                error_msg = f"Errore batch {batch_num}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
    
    return {
        "migrated": migrated,
        "errors": errors,
        "total": total_recipes
    }

def compare_databases() -> dict:
    """
    Confronta i contenuti di ChromaDB e Elysia
    
    Returns:
        Statistiche comparative
    """
    chroma_stats = chroma_recipe_db.get_stats() if chroma_recipe_db.collection else {"total_recipes": 0}
    elysia_stats = elysia_recipe_db.get_stats() if elysia_recipe_db.collection else {"total_recipes": 0}
    
    return {
        "chromadb": {
            "recipes": chroma_stats.get("total_recipes", 0),
            "status": chroma_stats.get("status", "non disponibile")
        },
        "elysia": {
            "recipes": elysia_stats.get("total_recipes", 0),
            "status": elysia_stats.get("status", "non disponibile")
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Migra ricette da ChromaDB a Elysia/Weaviate")
    parser.add_argument("--dry-run", action="store_true", help="Simula la migrazione senza effettuare modifiche")
    parser.add_argument("--batch-size", type=int, default=10, help="Numero di ricette per batch (default: 10)")
    parser.add_argument("--compare", action="store_true", help="Confronta i database senza migrare")
    
    args = parser.parse_args()
    
    logger.info("=== MIGRAZIONE SMART RECIPE: ChromaDB → Elysia/Weaviate ===")
    
    # Confronto database
    if args.compare:
        comparison = compare_databases()
        logger.info("Stato attuale dei database:")
        logger.info(f"ChromaDB: {comparison['chromadb']['recipes']} ricette ({comparison['chromadb']['status']})")
        logger.info(f"Elysia: {comparison['elysia']['recipes']} ricette ({comparison['elysia']['status']})")
        return
    
    # Carica ricette dal disco
    recipes = load_recipes_from_disk()
    
    if not recipes:
        logger.error("Nessuna ricetta trovata da migrare")
        return
    
    logger.info(f"Trovate {len(recipes)} ricette da migrare")
    
    # Esegui migrazione
    try:
        results = migrate_recipes_to_elysia(
            recipes=recipes,
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        
        # Stampa risultati
        logger.info("=== RISULTATI MIGRAZIONE ===")
        logger.info(f"Ricette totali: {results['total']}")
        logger.info(f"Ricette migrate: {results['migrated']}")
        logger.info(f"Errori: {len(results['errors'])}")
        
        if results['errors']:
            logger.warning("Errori riscontrati:")
            for error in results['errors']:
                logger.warning(f"  - {error}")
        
        if not args.dry_run:
            # Confronto post-migrazione
            comparison = compare_databases()
            logger.info("Stato post-migrazione:")
            logger.info(f"ChromaDB: {comparison['chromadb']['recipes']} ricette")
            logger.info(f"Elysia: {comparison['elysia']['recipes']} ricette")
        
        logger.info("Migrazione completata!")
        
    except Exception as e:
        logger.error(f"Errore durante la migrazione: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
