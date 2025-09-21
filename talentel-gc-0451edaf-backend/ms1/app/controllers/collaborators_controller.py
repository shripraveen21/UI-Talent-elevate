from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from ..config.database import get_db
from ..models.models import RoleEnum, Employee, Collaborator
from ..services.rbac_service import RBACService, require_roles
from typing import List
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..schemas.schemas import CollaboratorOut

router = APIRouter()


bearer_scheme=HTTPBearer()
@router.get("/me/permissions", response_model=dict)
def get_user_permissions(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    payload = RBACService.get_current_user(credentials)
    email = payload.get("sub")
    role = payload.get("role")

    # Default permissions
    permissions = {
        "role": role,
        "isCollaborator": False,
        "test_assign": False,
        "test_create": False,
        "topics": False,
        # Add more permission fields as needed
    }

    # CapabilityLeader and ProductManager get all permissions
    if role in [RoleEnum.CapabilityLeader.value, RoleEnum.ProductManager.value]:
        permissions["test_assign"] = True
        permissions["test_create"] = True
        permissions["topics"] = True
        return permissions

    # Check if user is a collaborator
    user = db.query(Employee).filter(Employee.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Aggregate permissions across all Collaborator records for this user
    collab_records = db.query(Collaborator).filter(Collaborator.collaborator_id == user.user_id).all()
    if collab_records:
        permissions["isCollaborator"] = True
        # If any record has topics=True, grant topics permission
        permissions["topics"] = any(getattr(c, "topics", False) for c in collab_records)
        # For test_assign and test_create, you may want similar aggregation or keep as is
        permissions["test_assign"] = any(getattr(c, "test_assign", False) for c in collab_records)
        permissions["test_create"] = any(getattr(c, "test_create", False) for c in collab_records)
        # Add more permissions as needed

    return permissions


@router.get("/get-collaborators", response_model=List[CollaboratorOut])
def get_all_collaborators(
        db: Session = Depends(get_db),
        curr_user = Depends(require_roles(RoleEnum.CapabilityLeader)),
):
    try:
        user = db.query(Employee).filter(
            Employee.email == curr_user.get('sub')
        ).first()
        if not user:
            raise HTTPException(status_code=401, detail="Forbidden")

        # Get all collaborator records for this user
        collab_records = db.query(Collaborator).filter(
            Collaborator.cl_id == user.user_id
        ).all()

        # For each collaborator record, get the employee info and permissions
        result = []
        for collab in collab_records:
            emp = db.query(Employee).filter(
                Employee.user_id == collab.collaborator_id
            ).first()
            if emp:
                result.append({
                    "email": emp.email,
                    "collaborator_id": emp.user_id,
                    "topics": collab.topics,
                    "test_create": collab.test_create,
                    "test_assign": collab.test_assign
                })
        return result

    except HTTPException as err:
        raise err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



class AddCollaborator(BaseModel):
    collaborator_email: str
    topics: bool = False
    test_create: bool = False
    test_assign: bool = False


@router.post("/upsert-collaborator")
def upsert_collaborator(
    request: AddCollaborator,
    db: Session = Depends(get_db),
    curr_user=Depends(require_roles(RoleEnum.CapabilityLeader))
):
    try:
        user = db.query(Employee).filter(
            Employee.email == curr_user.get('sub')
        ).first()
        if not user:
            raise HTTPException(status_code=401, detail="Forbidden")

        collaborator = db.query(Employee).filter(
            Employee.email == request.collaborator_email
        ).first()
        if not collaborator:
            raise HTTPException(status_code=404, detail="Employee not found")

        collab_record = db.query(Collaborator).filter(
            Collaborator.collaborator_id == collaborator.user_id,
            Collaborator.cl_id == user.user_id
        ).first()

        if collab_record:
            collab_record.topics = request.topics
            collab_record.test_create = request.test_create
            collab_record.test_assign = request.test_assign
            db.commit()
            db.refresh(collab_record)
            return collab_record
        else:
            new_collaborator = Collaborator(
                collaborator_id=collaborator.user_id,
                cl_id=user.user_id,
                topics=request.topics,
                test_create=request.test_create,
                test_assign=request.test_assign,
            )
            db.add(new_collaborator)
            db.commit()
            db.refresh(new_collaborator)
            return new_collaborator

    except HTTPException as err:
        raise err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-collaborator")
def delete_collaborator(
    collaborator_email: str,
    db: Session = Depends(get_db),
    curr_user=Depends(require_roles(RoleEnum.CapabilityLeader))
):
    try:
        user = db.query(Employee).filter(
            Employee.email == curr_user.get('sub')
        ).first()
        if not user:
            raise HTTPException(status_code=401, detail="Forbidden")

        collaborator = db.query(Employee).filter(
            Employee.email == collaborator_email
        ).first()
        if not collaborator:
            raise HTTPException(status_code=404, detail="Collaborator employee not found")

        collab_record = db.query(Collaborator).filter(
            Collaborator.collaborator_id == collaborator.user_id,
            Collaborator.cl_id == user.user_id
        ).first()
        if not collab_record:
            raise HTTPException(status_code=404, detail="Collaborator relationship not found")

        db.delete(collab_record)
        db.commit()
        return {"detail": "Collaborator deleted successfully"}

    except HTTPException as err:
        raise err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/is-collaborator")
def is_collaborator(
        db: Session = Depends(get_db),
        curr_user = Depends(RBACService.get_current_user)
):
    try:
        user = db.query(Employee).filter(
            Employee.email == curr_user.get('sub')
        ).first()
        if not user:
            raise HTTPException(status_code=401, detail="Forbidden")
        collaborators = db.query(Collaborator).filter(
            Collaborator.collaborator_id == user.user_id,
        ).first()
        if not collaborators:
            return False
        return True
    except Exception as err:
        print(err)
        raise HTTPException(status_code=500, detail=str(err))