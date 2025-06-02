from pydantic import BaseModel, Field
from typing import List, Optional

class GetIrSchema(BaseModel):
    ir_id:str
    # ir_name:str
    # ir_email:Optional[str] = Field(default="Email Address")

class GetListIrSchema(BaseModel):
    results: List[GetIrSchema]

class createIrSchema(BaseModel):
    ir_id : str
