from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..services.auth_service import AuthService
from ..models.models import Employee, RoleEnum
from ..schemas.schemas import EmployeeCreate, EmployeeLogin, EmployeeOut
from ..services.auth_service import AuthService
from ..services.rbac_service import RBACService
from ..config.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Employee).filter(Employee.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not AuthService.verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token_data = {"sub": user.email, "role": str(user.role.value) if hasattr(user.role, "value") else str(user.role)}
    access_token = AuthService.create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# @router.get("/getCurrentUser", response_model=EmployeeOut)
# def get_me(user=Depends(RBACService.get_current_user), db: Session = Depends(get_db)):
#     db_user = db.query(Employee).filter(Employee.user_id == user["user_id"]).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user

@router.get("/getCurrentUser", response_model=EmployeeOut)
def get_me(user=Depends(RBACService.get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
