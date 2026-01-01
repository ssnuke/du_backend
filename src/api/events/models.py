from sqlmodel import SQLModel, Field,Relationship
from typing import List, Optional,Annotated
from datetime import datetime, timedelta
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
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'dreamersunited_db'
  AND pid <> pg_backend_pid();
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
PasswordStr = Annotated[str, Field(min_length=8, max_length=256, title="IR Password")]

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
    weekly_info_done: Optional[int] = Field(default=0, title="Team Weekly Info Done")
    weekly_plan_done: Optional[int] = Field(default=0, title="Team Weekly Plan Done")
    # Aggregated targets (computed, but you can store for reporting/caching)
    weekly_info_target: Optional[int] = Field(default=0, title="Team Weekly Info Target")
    weekly_plan_target: Optional[int] = Field(default=0, title="Team Weekly Plan Target")
    # UV target is only for LDC/LS, not for team as a whole

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
    # Add these fields:
    weekly_info_target: Optional[int] = Field(default=0, title="Weekly Info Target")
    weekly_plan_target: Optional[int] = Field(default=0, title="Weekly Plan Target")
    weekly_uv_target: Optional[int] = Field(default=None, title="Weekly UV Target")  # Only for LDC/LS
    # UV target is not for IRs, so do not add here

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


# Plan detail records (parallel to InfoDetailModel)
class PlanDetailModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ir_id: str = Field(foreign_key="irmodel.ir_id")
    plan_date: datetime = Field(default_factory=lambda: datetime.now(IST), title="Plan Date")
    plan_name: Optional[str] = Field(title="Plan Description")
    comments: Optional[str] = Field(title="Comments")


# Model to store weekly snapshots for teams. Each record represents a week's totals
class TeamWeekModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teammodel.id")
    week_start: datetime = Field(title="Week Start Datetime (IST)")
    weekly_info_done: int = Field(default=0, title="Archived weekly info done")
    weekly_plan_done: int = Field(default=0, title="Archived weekly plan done")
    created_at: datetime = Field(default_factory=lambda: datetime.now(IST), title="Record created at (IST)")


def get_current_week_start(now: Optional[datetime] = None) -> datetime:
    """
    Compute the current week start datetime using Friday 21:31 IST as the week boundary.
    Returns the datetime (in IST tzinfo) for the most recent Friday 21:31 that is <= now.
    """
    if now is None:
        now = datetime.now(IST)
    else:
        # ensure timezone-aware in IST
        try:
            now = now.astimezone(IST)
        except Exception:
            now = datetime.now(IST)

    # weekday(): Monday=0 ... Sunday=6. Friday == 4
    days_since_friday = (now.weekday() - 4) % 7
    candidate = now - timedelta(days=days_since_friday)
    candidate = candidate.replace(hour=21, minute=31, second=0, microsecond=0)
    # If candidate is in the future relative to now, subtract 7 days
    if now < candidate:
        candidate = candidate - timedelta(days=7)
    return candidate