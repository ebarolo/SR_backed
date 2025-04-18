from pydantic import BaseModel
from typing import List, Optional

class Ingredient(BaseModel):
    name: str
    qt: float
    um: str

class RecipeDBSchema(BaseModel):
    title: str
    category: List[str]
    preparation_time: Optional[int]
    cooking_time: Optional[int]
    ingredients: str
    recipe_step: str
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
    video_path: Optional[str]
 
class RecipeAIResponse(BaseModel):
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