import os 
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from .models import GetIrSchema,GetListIrSchema,IrIdValidation,IrModel,IrLoginValidation,TeamModel,TeamMemberLink,CreateTeamValidation,AssignIrValidation,InfoDetailModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from api.db.session import get_session
from sqlmodel import Session, select
from .models import IrIdModel
from passlib.hash import bcrypt
from enum import Enum
from api.db.session import reset_db
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List


router = APIRouter()

class TeamRole(str, Enum):
    LDC = "LDC"
    LS = "LS"
    GC = "GC"
    IR = "IR"

#GET Requests
"""
Fetches all IR (IrIdModel) records from the database.

Args:
    session (Session): SQLAlchemy session dependency.

Returns:
    List[IrIdModel]: A list of all IR records.

Raises:
    HTTPException: If an error occurs during database query, returns a 500 status code with error details.
"""
@router.get("/get_all_ir")
def get_all_ir(session:Session=Depends(get_session)):
    try:
        query = select(IrIdModel) #.order_by(IrIdModel.ir_id.desc()) #.limit(10)
        results = session.exec(query).all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail={"Error": str(e)})

"""
Fetch a single IR (Incident Report) by its ID.

Args:
    fetch_ir_id (str): The ID of the IR to retrieve.
    session (Session, optional): Database session dependency.

Returns:
    IrModel: The IR object corresponding to the given ID.

Raises:
    HTTPException: If no IR is found with the specified ID, returns a 404 error.
"""
@router.get("/ir/{fetch_ir_id}")
def get_single_ir(fetch_ir_id:str ,session:Session=Depends(get_session)):
    query = select(IrModel).where(IrModel.ir_id == fetch_ir_id)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="IR ID Not Found!")
    return result

"""
Fetches all registered IR (Incident Report) records from the database.
Args:
    session (Session): SQLModel session dependency for database access.
Returns:
    JSONResponse: A JSON response containing a list of IR records and their count.
                  On error, returns a JSON response with error details and status code 500.
"""
@router.get("/irs")
def get_all_registered_ir(session: Session = Depends(get_session)):
    try:
        query = select(IrModel)
        results = session.exec(query).all()
        
        # Convert ORM objects to dictionaries
        data = [r.dict() for r in results]
        
        return JSONResponse(content={"data": data, "count": len(data)})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
    
"""
Fetches all teams from the database.

Args:
    session (Session, optional): SQLModel session dependency for database access.

Returns:
    JSONResponse: A JSON response containing a list of all teams with status code 200.

Raises:
    HTTPException: If an unexpected error occurs during database access, returns a 500 status code with error details.
"""    
@router.get("/teams")
def get_all_teams(session: Session = Depends(get_session)):
    try:
        teams = session.exec(select(TeamModel)).all()
        result = [team.model_dump() for team in teams]
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error Occured {str(e)}")


"""
Fetches all unique LDC (Local Data Coordinator) members and their details.

This endpoint retrieves all team member links with the role of LDC, extracts their unique IR IDs,
fetches corresponding IrModel objects, and returns a serialized list of LDCs with their IR ID and name.

Args:
    session (Session): Database session dependency.

Returns:
    JSONResponse: A list of dictionaries containing 'ir_id', 'ir_name', and 'id' for each LDC.

Raises:
    HTTPException: If an unexpected error occurs during processing.
"""
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

"""
Fetches all teams associated with a given LDC (Local District Coordinator) ID.

Args:
    ldc_id (str): The ID of the LDC to filter teams by.
    session (Session, optional): Database session dependency.

Returns:
    JSONResponse: A JSON response containing a list of teams associated with the specified LDC ID.

Raises:
    HTTPException: If an unexpected error occurs during database query or processing.
"""
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


"""
Retrieve all members of a specified team.

Args:
    team_id (int): The ID of the team whose members are to be retrieved.
    session (Session, optional): Database session dependency.

Returns:
    JSONResponse: A list of serialized team member objects with status code 200.

Raises:
    HTTPException: If an error occurs during retrieval, returns status code 500 with error details.
"""
@router.get("/team_members/{team_id}")
def get_team_members(team_id: int, session: Session = Depends(get_session)):
    try:
        members = session.exec(
            select(TeamMemberLink).where(TeamMemberLink.team_id == team_id)
        ).all()
        # Serialize each member to dict
        return JSONResponse(
            status_code=200,
            content=[member.model_dump() for member in members]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")

#Get info details for an IR
"""
Fetches information details for a given IR ID.

Args:
    ir_id (str): The IR ID for which to retrieve information details.
    session (Session, optional): Database session dependency.

Returns:
    JSONResponse: A JSON response containing a list of info details with 'info_date' fields converted to ISO format strings.

Raises:
    HTTPException: If an unexpected error occurs during retrieval.
"""
@router.get("/info_details/{ir_id}")
def get_info_details(
    ir_id: str,
    from_date: str = None,
    to_date: str = None,
    session: Session = Depends(get_session)
):
    try:
        # If no date filters, default to today's data
        if not from_date and not to_date:
            today = datetime.now().date()
            query = select(InfoDetailModel).where(
                InfoDetailModel.ir_id == ir_id,
                InfoDetailModel.info_date >= today,
                InfoDetailModel.info_date < today + timedelta(days=1)
            )
        else:
            # Parse dates if provided
            if from_date:
                from_dt = datetime.fromisoformat(from_date).date()
            else:
                from_dt = datetime.min.date()
            if to_date:
                to_dt = datetime.fromisoformat(to_date).date()
            else:
                to_dt = datetime.max.date()
            query = select(InfoDetailModel).where(
                InfoDetailModel.ir_id == ir_id,
                InfoDetailModel.info_date >= from_dt,
                InfoDetailModel.info_date <= to_dt
            )
        info_details = session.exec(query).all()
        result = []
        for info in info_details:
            data = info.model_dump()
            if isinstance(data.get("info_date"), datetime):
                data["info_date"] = data["info_date"].isoformat()
            result.append(data)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error Occured {str(e)}")
#Get info details for an IR
#GET Requests


#POST Requests
"""
Adds a new IR ID to the database.

This endpoint receives a payload containing IR ID data, validates it, and inserts it into the database.
On successful insertion, the newly created IR ID object is returned.
Handles validation errors and unexpected exceptions, returning appropriate HTTP error responses.

Args:
    payload (IrIdValidation): The IR ID data to be added, validated against the IrIdValidation schema.
    session (Session, optional): Database session dependency.

Returns:
    GetIrSchema: The newly created IR ID object.

Raises:
    HTTPException: 
        - 422 if validation fails.
        - 500 for unexpected errors during database operations.
"""
@router.post("/add_ir_id", response_model=GetIrSchema)
def add_ir_id(payload: IrIdValidation, session: Session = Depends(get_session)):
    try:
        print(payload)
        data = payload.model_dump()
        try:
            # obj = IrIdModel.model_validate(data)
            obj = IrIdModel(**data) 
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
"""
Registers a new IR (Incident Reporter) in the system.

Workflow:
    1. Checks if the provided IR ID exists in the IrIdModel table.
    2. If the IR ID exists, hashes the IR password and registers the IR with all provided details.
    3. If the IR ID does not exist, raises a 404 error ("IR ID Not Found!").

Args:
    payload (IrModel): The IR registration details.
    session (Session, optional): Database session dependency.

Raises:
    HTTPException: 
        - 404 if IR ID is not found.
        - 422 if there is a database integrity error.
        - 500 for any unexpected errors.

Returns:
    JSONResponse: Success message and registered IR ID on successful registration.
"""
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


"""
Handles IR login requests.
Args:
    payload (IrLoginValidation): The login credentials containing IR ID and password.
    session (Session, optional): The database session dependency.
Raises:
    HTTPException: If IR ID is not found (404).
    HTTPException: If password is invalid (401).
    HTTPException: For any other internal server errors (500).
Returns:
    JSONResponse: A response with status code 201 and IR data on successful login.
"""
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

"""
Creates a new team in the database.

Args:
    payload (CreateTeamValidation): The validated payload containing the team name.
    session (Session, optional): The database session, injected by dependency.

Returns:
    JSONResponse: A response with status code 201, containing a message, the created team's ID, and name.

Raises:
    HTTPException: If an error occurs during team creation, returns a 500 status code with the error detail.
"""
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

#Add IR to Team with Role
"""
Assigns an IR (Incident Responder) to a team with a specified role.

Args:
    payload (AssignIrValidation): The request payload containing ir_id, team_id, and role.
    session (Session, optional): Database session dependency.

Raises:
    HTTPException: If the IR is already assigned to the team (409 Conflict).
    HTTPException: For unexpected errors during assignment (500 Internal Server Error).

Returns:
    JSONResponse: Success message with status code 201 if assignment is successful.
"""
@router.post("/add_ir_to_team")
def add_ir_to_team(payload: AssignIrValidation, session: Session = Depends(get_session)):
    try:
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

#Add Info Detail for an IR
"""
Adds a new info detail entry associated with a given IR (Incident Report) ID.
Args:
    ir_id (str): The ID of the IR to associate the info detail with.
    payload (InfoDetailModel): The info detail data to be added.
    session (Session, optional): The database session dependency.
Raises:
    HTTPException: If the IR is not found (404) or if an unexpected error occurs (500).
Returns:
    JSONResponse: A response containing a success message and the newly created info detail ID.
"""
@router.post("/add_info_detail/{ir_id}")
def add_info_detail(ir_id: str, payload: List[InfoDetailModel], session: Session = Depends(get_session)):
    try:
        ir = session.get(IrModel, ir_id)
        if not ir:
            raise HTTPException(status_code=404, detail="IR not found")
        
        created_ids = []
        for info in payload:
            info_detail = InfoDetailModel(
                ir_id=ir_id,
                info_date=info.info_date,
                response=info.response,
                comments=info.comments,
                info_name=info.info_name
            )
            session.add(info_detail)
            session.commit()
            session.refresh(info_detail)
            created_ids.append(info_detail.id)
        
        return JSONResponse(
            status_code=201,
            content={"message": "Info details added", "info_ids": created_ids}
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
#Add Info Detail for an IR

#POST Requests

#PUT Requests
"""
Updates the details of an IR (Incident Report) identified by the given IR ID.
Args:
    update_ir (str): The IR ID to update.
    session (Session, optional): Database session dependency.
Raises:
    HTTPException: If the IR ID is not found in the database (404).
Returns:
    None
"""
@router.put("/{update_ir}")
def update_ir_details(update_ir:str,session:Session=Depends(get_session)):
    query = select(IrIdModel).where(IrIdModel.ir_id == update_ir)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="IR ID Not Found!")
    
    return None

#Update info details for an IR
"""
Updates an existing InfoDetailModel record with new details.
Args:
    info_id (int): The ID of the info detail to update.
    payload (InfoDetailModel): The updated info detail data.
    session (Session, optional): SQLAlchemy session dependency.
Raises:
    HTTPException: If the info detail is not found (404).
    HTTPException: If an unexpected error occurs during update (500).
Returns:
    JSONResponse: Success message and updated info_id if update is successful.
"""
@router.put("/update_info_detail/{info_id}")
def update_info_detail(info_id: int, payload: InfoDetailModel, session: Session = Depends(get_session)):
    try:
        info_detail = session.get(InfoDetailModel, info_id)
        if not info_detail:
            raise HTTPException(status_code=404, detail="Info detail not found")
        
        info_detail.info_date = payload.info_date
        info_detail.response = payload.response
        info_detail.comments = payload.comments
        info_detail.info_name = payload.info_name
        
        session.add(info_detail)
        session.commit()
        session.refresh(info_detail)
        
        return JSONResponse(
            status_code=200,
            content={"message": "Info detail updated", "info_id": info_detail.id}
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
#Update info details for an IR

#PUT Requests


#UPDATE Requests

"""
Updates the name of a team with the given team ID.

Args:
    team_id (int): The ID of the team to update.
    payload (CreateTeamValidation): The request body containing the new team name.
    session (Session, optional): The database session dependency.

Returns:
    JSONResponse: A response containing a success message, team ID, old name, and new name.

Raises:
    HTTPException: If the team is not found (404) or if an error occurs during the update (500).
"""
@router.patch("/update_team_name/{team_id}")
def update_team_name(team_id: int, payload: CreateTeamValidation, session: Session = Depends(get_session)):
    try:
        team = session.get(TeamModel, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        old_name = team.name
        team.name = payload.name
        session.add(team)
        session.commit()
        session.refresh(team)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Team name updated",
                "team_id": team.id,
                "old_name": old_name,
                "new_name": team.name
            }
        )
    except Exception as e:
        print("Error occured while updating team data - ",e)
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

#UPDATE Requests

#DELETE Requests
"""
Resets the database by calling the reset_db function.

Returns:
    dict: A dictionary containing the status and a success message if the reset is successful.

Raises:
    HTTPException: If an exception occurs during the reset process, raises an HTTPException with status code 500 and the error details.
"""
@router.post("/reset_database")
def reset_database():
    try:
        reset_db()
        return {"status": "success", "message": "Database has been reset successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
Deletes a team and its associated TeamMemberLink entries from the database.
Args:
    team_id (int): The ID of the team to delete.
    session (Session, optional): Database session dependency.
Raises:
    HTTPException: If the team is not found (404) or an unexpected error occurs (500).
Returns:
    JSONResponse: Confirmation message upon successful deletion.
"""
@router.delete("/delete_team/{team_id}")
def delete_team(team_id: int, session: Session = Depends(get_session)):
    try:
        team = session.get(TeamModel, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Delete associated TeamMemberLink entries
        session.exec(
            select(TeamMemberLink).where(TeamMemberLink.team_id == team_id)
        ).all()
        session.delete(team)
        session.commit()
        return JSONResponse(
            status_code=200,
            content={"message": f"Team with ID {team_id} has been deleted"}
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")

#Remove IR from Team
"""
Removes an IR (Individual Resource) from a specified team.

Args:
    team_id (int): The ID of the team from which the IR should be removed.
    ir_id (str): The ID of the IR to be removed.
    session (Session, optional): Database session dependency.

Returns:
    JSONResponse: A success message if the IR is removed.

Raises:
    HTTPException: 
        - 404 if the IR is not found in the team.
        - 500 for unexpected errors during the operation.
"""
@router.delete("/remove_ir_from_team/{team_id}/{ir_id}")
def remove_ir_from_team(team_id: int, ir_id: str, session: Session = Depends(get_session)):
    try:
        link = session.exec(
            select(TeamMemberLink).where(
                TeamMemberLink.team_id == team_id,
                TeamMemberLink.ir_id == ir_id
            )
        ).first()
        if not link:
            raise HTTPException(status_code=404, detail="IR not found in team")
        session.delete(link)
        session.commit()
        return JSONResponse(
            status_code=200,
            content={"message": f"IR '{ir_id}' removed from team {team_id}"}
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    

#Delete info detail for an IR

"""
Deletes an InfoDetail record by its ID.
Args:
    info_id (int): The ID of the InfoDetail to delete.
    session (Session, optional): SQLAlchemy session dependency.
Raises:
    HTTPException: If the InfoDetail is not found (404).
    HTTPException: If an unexpected error occurs during deletion (500).
Returns:
    JSONResponse: Success message indicating the InfoDetail has been deleted.
"""
@router.delete("/delete_info_detail/{info_id}")
def delete_info_detail(info_id: int, session: Session = Depends(get_session)):  
    try:
        info_detail = session.get(InfoDetailModel, info_id)
        if not info_detail:
            raise HTTPException(status_code=404, detail="Info detail not found")
        
        session.delete(info_detail)
        session.commit()
        
        return JSONResponse(
            status_code=200,
            content={"message": f"Info detail with ID {info_id} has been deleted"}
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
#Delete info detail for an IR