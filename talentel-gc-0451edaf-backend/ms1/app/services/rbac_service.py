from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os
import jwt
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..models.models import RoleEnum, Employee, Collaborator

bearer_scheme = HTTPBearer()

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable not set")

class RBACService:
    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation error: {str(e)}"
            )

    @staticmethod
    def require_role(credentials: HTTPAuthorizationCredentials, allowed_roles):
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
            user_role = payload.get("role")
            allowed_role_values = [role.value for role in allowed_roles]
            if user_role not in allowed_role_values:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this resource"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation error: {str(e)}"
            )

def get_capability_leader_if_not_self(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    payload = RBACService.get_current_user(credentials)
    email = payload.get("sub")
    user_role = payload.get("role")

    # Fetch the current user
    user = db.query(Employee).filter(Employee.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    # If current user is capability leader, return self
    if user_role == RoleEnum.CapabilityLeader.value:
        return user

    # Otherwise, find the capability leader via Collaborator relationship
    collaborator_record = db.query(Collaborator).filter(
        Collaborator.collaborator_id == user.user_id
    ).first()

    if not collaborator_record:
        raise HTTPException(status_code=404, detail="Capability leader relationship not found")

    capability_leader = db.query(Employee).filter(
        Employee.user_id == collaborator_record.cl_id
    ).first()

    if not capability_leader:
        raise HTTPException(status_code=404, detail="Capability leader not found")

    return capability_leader
        
def require_roles(*roles):
    def dependency(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
        return RBACService.require_role(credentials, roles)
    return dependency