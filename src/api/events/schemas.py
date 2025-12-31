from pydantic import BaseModel
from typing import List
from .models import TeamRole

#Validation Schemas
class IrIdValidation(BaseModel):
    ir_id : str

class GetIrSchema(BaseModel):
    ir_id:str

class GetListIrSchema(BaseModel):
    results: List[GetIrSchema]

class IrLoginValidation(BaseModel):
    ir_id:str
    ir_password:str 

class CreateTeamValidation(BaseModel):
    name:str   

class AssignIrValidation(BaseModel):
    ir_id:str
    team_id:int
    role:TeamRole
#Validation Schemas