from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Ingredient(BaseModel):
    name: str
    qt: float
    um: str

class RecipeDBSchema(BaseModel):
    title: str
    category: List[str]
    preparation_time: Optional[int]
    cooking_time: Optional[int]
    ingredients: List[Ingredient]
    recipe_step: List[str]
    description: str
    diet: Optional[str]
    technique: Optional[str] 
    language: str
    chef_advise: Optional[str]
    tags: Optional[List[str]]
    nutritional_info: Optional[List[str]] 
    cuisine_type: Optional[str] 
    ricetta_audio: Optional[str]
    ricetta_caption: Optional[str] 
    shortcode: str
 
class RecipeResponse(BaseModel):
    _id: str
    title: str
    description: str
    category: List[str]
    cuisine_type: str
    ingredients: List[Ingredient]
    recipe_step: List[str]
    preparation_time: int
    cooking_time: int
    tags: List[str]
    chef_advise: Optional[str]
    shortcode: str
    match_score: float = Field(..., description="Score di rilevanza della ricetta")
  
recipe_schema = {
  "name": "recipe_schema",
  "schema": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "description": "The title of the recipe."
      },
      "category": {
        "type": "array",
        "description": "The categories the recipe belongs to.",
        "items": {
          "type": "string"
        }
      },
      "preparation_time": {
        "type": "number",
        "description": "The preparation time in minutes."
      },
      "cooking_time": {
        "type": "number",
        "description": "The cooking time in minutes."
      },
      "ingredients": {
        "type": "array",
        "description": "The list of ingredients required for the recipe.",
        "items": {
          "$ref": "#/$defs/ingredient"
        }
      },
      "recipe_step": {
        "type": "array",
        "description": "Step-by-step instructions for preparing the recipe.",
        "items": {
          "type": "string"
        }
      },
      "description": {
        "type": "string",
        "description": "A short description of the recipe."
      },
      "diet": {
        "type": "string",
        "description": "Diet type associated with the recipe."
      },
      "technique": {
        "type": "string",
        "description": "Cooking technique used in the recipe."
      },
      "language": {
        "type": "string",
        "description": "The language of the recipe."
      },
      "chef_advise": {
        "type": "string",
        "description": "Advice or tips from the chef."
      },
      "tags": {
        "type": "array",
        "description": "Tags related to the recipe.",
        "items": {
          "type": "string"
        }
      },
      "nutritional_info": {
        "type": "array",
        "description": "Nutritional information pertaining to the recipe.",
        "items": {
          "type": "string"
        }
      },
      "cuisine_type": {
        "type": "string",
        "description": "Type of cuisine the recipe represents."
      }
    },
    "required": [
      "title",
      "category",
      "preparation_time",
      "cooking_time",
      "ingredients",
      "recipe_step",
      "description",
      "diet",
      "technique",
      "language",
      "chef_advise",
      "tags",
      "nutritional_info",
      "cuisine_type"
    ],
    "additionalProperties": False,
    "$defs": {
      "ingredient": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "The name of the ingredient."
          },
          "qt": {
            "type": "number",
            "description": "The quantity of the ingredient."
          },
          "um": {
            "type": "string",
            "description": "The unit of measurement for the ingredient."
          }
        },
        "required": [
          "name",
          "qt",
          "um"
        ],
        "additionalProperties": False
      }
    }
  },
  "strict": True
}