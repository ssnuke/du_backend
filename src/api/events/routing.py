import os 
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from .models import GetIrSchema,GetListIrSchema,IrIdValidation,IrModel,IrLoginValidation,TeamModel,TeamMemberLink,CreateTeamValidation,AssignIrValidation
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from api.db.session import get_session
from sqlmodel import Session, select
from .models import IrIdModel
from passlib.hash import bcrypt
from enum import Enum

router = APIRouter()

# @router.get("/")
# def send_add_ir_ids() -> GetListIrSchema:
#     print("Fetching all IR ID's!")
#     print(os.environ.get("DATABASE_URL"))
#     return {
#         "results": [{"id": 1,
#         "ir_name": 'Name comes here',},
#        { "id": 2,
#         "ir_name": 'Name comes here',},
#         { "id":33,
#         "ir_name": 'Name comes here',}]
#     }

# @router.get("/{ir_id}")
# def send_add_ir_id(ir_id: int) -> GetIrSchema:
#     print("Fetching IR ID details!")
#     return {
#         "id": ir_id,
#         "ir_name": 'Name comes here',
    # }

class TeamRole(str, Enum):
    LDC = "LDC"
    LS = "LS"
    GC = "GC"
    IR = "IR"

#GET Requests
@router.get("/get_all_ir")
def get_all_ir(session:Session=Depends(get_session)):
    try:
        query = select(IrIdModel) #.order_by(IrIdModel.ir_id.desc()) #.limit(10)
        results = session.exec(query).all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail={"Error": str(e)})

@router.get("/ir/{fetch_ir_id}")
def get_single_ir(fetch_ir_id:str ,session:Session=Depends(get_session)):
    query = select(IrIdModel).where(IrIdModel.ir_id == fetch_ir_id)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="IR ID Not Found!")
    return result

@router.get("/irs")
def get_all_registered_ir(session:Session=Depends(get_session)):
    try:
        query = select(IrModel)
        results = session.exec(query).all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail={"Error": str(e)})
    
@router.get("/ldcs")
def get_ldcs(session: Session = Depends(get_session)):
    try:
        ldcs_links = session.exec(
            select(TeamMemberLink).where(TeamMemberLink.role == TeamRole.LDC)
        ).all()

        # Step 2: Use a set to collect unique LDC ir_ids
        unique_ir_ids = set(link.ir_id for link in ldcs_links)

        # Step 3: Fetch IrModel objects for each unique LDC
        ldcs = session.exec(
            select(IrModel).where(IrModel.ir_id.in_(unique_ir_ids))
        ).all()

        # Step 4: Serialize result
        result = [{"ir_id": ldc.ir_id, "ir_name": ldc.ir_name, "id":ldc.ir_id} for ldc in ldcs]
        return JSONResponse(status_code=200,content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error Occured {str(e)}")

@router.get("/teams_by_ldc/{ldc_id}")
def get_teams_by_ldc(ldc_id: str, session: Session = Depends(get_session)):
    try:
        teams = session.exec(
            select(TeamModel).join(TeamMemberLink).where(
                TeamMemberLink.ir_id == ldc_id,
                TeamMemberLink.role == TeamRole.LDC
            )
        ).all()
        result = [team.model_dump()for team in teams]
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error Occured {str(e)}")

@router.get("/team_members/{team_id}")
def get_team_members(team_id: int, session: Session = Depends(get_session)):
    try:
        members = session.exec(
            select(TeamMemberLink).where(TeamMemberLink.team_id == team_id)
        ).all()
        return JSONResponse(status_code=200, content=members)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unexpected Error Occured")
#GET Requests


#POST Requests
@router.post("/add_ir_id", response_model=GetIrSchema)
def add_ir_id(payload: IrIdValidation, session: Session = Depends(get_session)):
    try:
        print(payload)
        data = payload.model_dump()
        try:
            obj = IrIdModel.model_validate(data)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
        except ValidationError as ve:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Validation error", "details": str(e)}
            )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500,detail={"error": "Unexpected error", "details": str(e)})

#Register IR 
@router.post("/register_new_ir")
def register_new_ir(payload: IrModel, session:Session=Depends(get_session)):
    '''
    1. Check if the IR ID exists in the IRIdModel
    2. If the yes, then go ahead and register the IR with all the details
    3. If no then, raise error IR ID not Found! 
    '''
    query = select(IrIdModel).where(IrIdModel.ir_id == payload.ir_id)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404,detail="IR ID Not Found!")
    else:
        data = payload.model_dump()
        data["ir_password"] = bcrypt.hash(data["ir_password"])
        try:
            obj = IrModel.model_validate(data)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return JSONResponse(status_code=201,content={"message": "IR registered successfully", "ir_id": obj.ir_id})
        except IntegrityError as e:
                session.rollback()
                raise HTTPException(
                    status_code=422,
                    detail={"error": "Database integrity error", "details": str(e)}
                )
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail={"error": "Unexpected error", "details": str(e)}
            )

@router.post("/login")
def ir_login(payload:IrLoginValidation,session:Session=Depends(get_session)):
    try:
        query = select(IrModel).where(IrModel.ir_id == payload.ir_id)
        result = session.exec(query).first()
        if not result:
            raise HTTPException(status_code=404, detail="IR ID Not Found!")
        
        if not bcrypt.verify(payload.ir_password, result.ir_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        ir_data = result.model_dump(exclude={"ir_password"})
        return JSONResponse(status_code=201,content={"message":"Login Successful", "ir":ir_data})
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500,detail=str(e))

@router.post("/create_team")
def create_team(payload:CreateTeamValidation, session: Session = Depends(get_session)):
    try:
        team = TeamModel(name=payload.name)
        session.add(team)
        session.commit()
        session.refresh(team)
        return JSONResponse(status_code=201, content={"message": "Team created", "team_id": team.id,"team_name": team.name})
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))        

@router.post("/assign_ir_to_team")
def assign_ir_to_team(payload: AssignIrValidation, session: Session = Depends(get_session)):
    try:
        # Step 1: Check if the IR is already assigned to the same team
        existing = session.exec(
            select(TeamMemberLink).where(
                TeamMemberLink.ir_id == payload.ir_id,
                TeamMemberLink.team_id == payload.team_id
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"IR '{payload.ir_id}' is already assigned to team {payload.team_id}"
            )

        # Step 2: Create new assignment
        link = TeamMemberLink(
            ir_id=payload.ir_id,
            team_id=payload.team_id,
            role=payload.role
        )
        session.add(link)
        session.commit()

        return JSONResponse(
            status_code=201,
            content={"message": f"{payload.role} assigned to team {payload.team_id}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")


#POST Requests

#PUT Requests
@router.put("/{update_ir}")
def update_ir_details(update_ir:str,session:Session=Depends(get_session)):
    query = select(IrIdModel).where(IrIdModel.ir_id == update_ir)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="IR ID Not Found!")
    
    return None
#PUT Requests


#DELETE Requests