from sqlmodel import SQLModel, Field,Relationship
from typing import List, Optional,Annotated
from datetime import datetime
import pytz
from pydantic import field_validator,EmailStr,constr
from enum import Enum

'''
Database URL for PostgreSQL
psql postgresql://db_user:eoOw0MT2IcJuq62UV82adBeYdeadGVQ3@dpg-d1tc4k8dl3ps739ajc50-a.singapore-postgres.render.com/dreamersunited_db
\l # List all databases
\c dreamersunited_db # Connect to the database
\dt # List all tables in the current database
\di # List all indexes in the current database
DROP DATABASE dreamersunited_db;
CREATE DATABASE dreamersunited_db;
'''


# Enum to define roles
class TeamRole(str, Enum):
    LDC = "LDC"
    LS = "LS"
    GC = "GC"
    IR = "IR"

class InfoResponse(str, Enum):
    A = "A"
    B = "B"
    C = "C"

IST = pytz.timezone("Asia/Kolkata")
PasswordStr = Annotated[str, Field(min_length=8, max_length=64, title="IR Password")]

#Helper Functions
def current_ist_date_str() -> str:
    now_ist = datetime.now(IST)
    return now_ist.strftime("%d-%m-%Y")
#Helper Functions

#Validation Schemas
class IrIdValidation(SQLModel):
    ir_id : str

class GetIrSchema(SQLModel):
    ir_id:str

class GetListIrSchema(SQLModel):
    results: List[GetIrSchema]

class IrLoginValidation(SQLModel):
    ir_id:str
    ir_password:str 

class CreateTeamValidation(SQLModel):
    name:str   

class AssignIrValidation(SQLModel):
    ir_id:str
    team_id:int
    role:TeamRole
#Validation Schemas

#SQL TABLES
class IrIdModel(SQLModel, table=True):
    ir_id: str = Field(primary_key=True, max_length=18)


# Team Model
class TeamModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, title="Team Name")
    # Relationships
    members: List["TeamMemberLink"] = Relationship(back_populates="team")

# Intermediate Table for IR-Team with Role
class TeamMemberLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teammodel.id")
    ir_id: str = Field(foreign_key="irmodel.ir_id")
    role: TeamRole = Field(title="Role in Team")
    # Relationships
    team: Optional["TeamModel"] = Relationship(back_populates="members")
    ir: Optional["IrModel"] = Relationship(back_populates="teams")

# Update your existing IR model with reverse relationship
class IrModel(SQLModel, table=True):
    ir_id: str = Field(primary_key=True, max_length=18, title="IR ID")
    ir_name: str = Field(max_length=45, title="IR Name")
    ir_email: EmailStr = Field(title="IR Email")
    ir_access_level: int = Field(default=5, title="IR Access Level", ge=1, le=5) #1= Admin, 2 = LDC, 3 = LS, 4 = GC , 5 = IR
    ir_password: PasswordStr
    status: bool = Field(default=True, title="IR Status")
    plan_count: Optional[int] = Field(title="Plan Count", default=0)
    dr_count: Optional[int] = Field(title="DRs", default=0)
    info_count: Optional[int] = Field(title="Info's Given", default=0)
    started_date: Optional[str] = Field(default_factory=current_ist_date_str, title="Started Date")
    name_list: Optional[int] = Field(title="Name List Count", default=0)

    teams: List["TeamMemberLink"] = Relationship(back_populates="ir")

    @field_validator("started_date", mode="before")
    @classmethod
    def validate_started_date(cls, v):
        if isinstance(v, datetime):
            return v.astimezone(IST).strftime("%d-%m-%Y")
        return v
    
class InfoDetailModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ir_id: str = Field(foreign_key="irmodel.ir_id")
    info_date: datetime = Field(default_factory=lambda: datetime.now(IST), title="Info Date")
    response: InfoResponse = Field(title="Response Option")
    comments: Optional[str] = Field(title="Comments")
    info_name: str = Field(title="Info Name of the Person")