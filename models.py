from pydantic import BaseModel

class ingredient(BaseModel):
 name:str
 qt:int
 um:str
   
class recipe(BaseModel):
  recipe_id: str
  title: str
  category: list[str]
  prepration_time: int
  cooking_time: int
  ingredients: list[ingredient]
  prepration_step: list[str]
  chef_advise: str
  tags:list[str]
  nutritional_info:list[str]
  cuisine_type:str
  ricetta_audio:str
  ricetta_caption:str
  ingredients_text:str
  video:str
  error:str