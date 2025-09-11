"""
Modelli Pydantic per Smart Recipe API.

Definisce gli schemi di validazione dati per ricette, ingredienti,
job di importazione e risposte API.

Author: Smart Recipe Team
Version: 0.7
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Ingredient(BaseModel):
    """Modello per ingrediente di una ricetta."""
    name: str  # Nome dell'ingrediente
    qt: float  # Quantità
    um: str    # Unità di misura

class RecipeDBSchema(BaseModel):
    """
    Schema completo per una ricetta nel database.
    
    Contiene tutti i campi necessari per memorizzare e indicizzare
    una ricetta nel sistema Weaviate/Elysia.
    """
    title: str                                # Titolo della ricetta
    category: List[str]                       # Categorie (primo, secondo, dolce, etc.)
    preparation_time: Optional[int]           # Tempo preparazione in minuti
    cooking_time: Optional[int]               # Tempo cottura in minuti
    ingredients: List[Ingredient]              # Lista ingredienti con quantità
    recipe_step: List[str]                    # Passaggi della ricetta
    description: str                          # Descrizione breve
    diet: Optional[str]                       # Tipo dieta (vegan, vegetarian, etc.)
    technique: Optional[str]                  # Tecnica di cottura principale
    language: str                             # Lingua della ricetta
    chef_advise: Optional[str]                # Consigli dello chef
    tags: Optional[List[str]]                 # Tag per ricerca
    nutritional_info: Optional[List[str]]     # Informazioni nutrizionali
    cuisine_type: Optional[str]               # Tipo di cucina (italiana, indiana, etc.)
    ricetta_audio: Optional[str]              # Path file audio ricetta
    ricetta_caption: Optional[str]            # Trascrizione/caption dal video
    shortcode: str                            # Identificativo univoco (da social media)
 
class RecipeResponse(BaseModel):
    """
    Schema per risposta API di ricerca ricette.
    
    Include i dati della ricetta più lo score di rilevanza
    dalla ricerca semantica.
    """
    _id: str                      # ID univoco nel database
    title: str                    # Titolo ricetta
    description: str              # Descrizione
    category: List[str]           # Categorie
    cuisine_type: str             # Tipo cucina
    ingredients: List[Ingredient] # Lista ingredienti
    recipe_step: List[str]        # Passaggi ricetta
    preparation_time: int         # Tempo preparazione
    cooking_time: int             # Tempo cottura
    tags: List[str]               # Tag
    chef_advise: Optional[str]    # Consigli chef
    shortcode: str                # Shortcode social
    match_score: float = Field(..., description="Score di rilevanza della ricetta")

class JobStatus(BaseModel):
    """
    Schema per stato di un job di importazione.
    
    Utilizzato per tracciare il progresso dell'importazione
    asincrona di ricette da URL video.
    """
    job_id: str                               # ID univoco del job
    status: str                               # Stato: queued, running, completed, failed
    detail: Optional[str] = None             # Dettagli errore o messaggio
    result: Optional[Dict[str, Any]] = None  # Risultati finali del job
    progress_percent: Optional[float] = None # Percentuale completamento
    progress: Optional[Dict[str, Any]] = None # Dettagli progresso per ogni URL
  
# Schema JSON per validazione ricette con OpenAI Structured Output
recipe_schema = {
    "name": "recipe",
    "schema": {
        "type": "object",
        "properties": {
            "numer_person": {
                "type": "integer",
                "description": "Numero di persone per cui è la ricetta"
            },
            "category": {
                "type": "array",
                "description": "Lista categorie della ricetta",
                "items": {
                    "type": "string"
                }
            },
            "chef_advise": {
                "type": "string",
                "description": "Consigli o suggerimenti dello chef"
            },
            "cooking_time": {
                "type": "integer",
                "description": "Tempo di cottura in minuti"
            },
            "cuisine_type": {
                "type": "string",
                "description": "Tipo di cucina (es. Italiana, Indiana)"
            },
            "description": {
                "type": "string",
                "description": "Descrizione breve della ricetta"
            },
            "diet": {
                "type": "string",
                "description": "Tipo di dieta (es. vegana, vegetariana, senza glutine)"
            },
            "ingredients": {
                "type": "array",
                "description": "Lista oggetti ingrediente",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nome dell'ingrediente"
                        },
                        "qt": {
                            "type": "number",
                            "description": "Quantità dell'ingrediente"
                        },
                        "um": {
                            "type": "string",
                            "description": "Unità di misura per la quantità"
                        }
                    },
                    "required": [
                        "name",
                        "qt",
                        "um"
                    ],
                    "additionalProperties": False
                }
            },
            "language": {
                "type": "string",
                "description": "Lingua della ricetta"
            },
            "nutritional_info": {
                "type": "array",
                "description": "Lista informazioni nutrizionali",
                "items": {
                    "type": "string"
                }
            },
            "preparation_time": {
                "type": "integer",
                "description": "Tempo di preparazione in minuti"
            },
            "recipe_step": {
                "type": "array",
                "description": "Lista ordinata dei passaggi di preparazione",
                "items": {
                    "type": "string"
                }
            },
            "tags": {
                "type": "array",
                "description": "Tag ricetta per ricerca o categorizzazione",
                "items": {
                    "type": "string"
                }
            },
            "technique": {
                "type": "string",
                "description": "Tecnica di cottura principale utilizzata"
            },
            "title": {
                "type": "string",
                "description": "Titolo della ricetta"
            }
        },
        "required": [
            "category",
            "numer_person",
            "chef_advise",
            "cooking_time",
            "cuisine_type",
            "description",
            "diet",
            "ingredients",
            "language",
            "nutritional_info",
            "preparation_time",
            "recipe_step",
            "tags",
            "technique",
            "title"
        ],
        "additionalProperties": False
    },
    "strict": True  # Forza validazione stretta OpenAI
}