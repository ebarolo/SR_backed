from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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

class JobStatus(BaseModel):
    job_id: str
    status: str
    detail: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    progress_percent: Optional[float] = None
    progress: Optional[Dict[str, Any]] = None
  
recipe_schema ={
  "name": "recipe",
  "schema": {
    "type": "object",
    "properties": {
      "category": {
        "type": "array",
        "description": "List of categories the recipe belongs to.",
        "items": {
          "type": "string"
        }
      },
      "chef_advise": {
        "type": "string",
        "description": "Advice or tip from the chef regarding the recipe."
      },
      "cooking_time": {
        "type": "integer",
        "description": "Cooking time in minutes."
      },
      "cuisine_type": {
        "type": "string",
        "description": "The cuisine type (e.g. Italian, Indian)."
      },
      "description": {
        "type": "string",
        "description": "Brief description of the recipe."
      },
      "diet": {
        "type": "string",
        "description": "Diet type (e.g. vegan, vegetarian, gluten-free)."
      },
      "ingredients": {
        "type": "array",
        "description": "List of ingredient objects.",
        "items": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "description": "Name of the ingredient."
            },
            "qt": {
              "type": "number",
              "description": "Quantity of the ingredient."
            },
            "um": {
              "type": "string",
              "description": "Unit of measure for the quantity."
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
        "description": "Language of the recipe."
      },
      "nutritional_info": {
        "type": "array",
        "description": "List of nutritional information strings.",
        "items": {
          "type": "string"
        }
      },
      "preparation_time": {
        "type": "integer",
        "description": "Preparation time in minutes."
      },
      "recipe_step": {
        "type": "array",
        "description": "Ordered list of recipe preparation steps.",
        "items": {
          "type": "string"
        }
      },
      "tags": {
        "type": "array",
        "description": "Recipe tags for search or categorization.",
        "items": {
          "type": "string"
        }
      },
      "technique": {
        "type": "string",
        "description": "Primary cooking technique used."
      },
      "title": {
        "type": "string",
        "description": "Recipe title."
      }
    },
    "required": [
      "category",
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
  "strict": True
}