from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services.rbac_service import RBACService, get_capability_leader_if_not_self
from ..models.models import RoleEnum

router = APIRouter(prefix="/rbac", tags=["rbac"])
bearer_scheme = HTTPBearer()

@router.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    # Only allow ProductManager and CapabilityLeader
    allowed_roles = [RoleEnum.ProductManager, RoleEnum.CapabilityLeader]
    payload = RBACService.require_role(credentials, allowed_roles)
    return {"message": "Access granted", "user": payload}

@router.get("/get-cl")
def get_capability_leader(
        curr_user = Depends(RBACService.get_current_user),
        cl = Depends(get_capability_leader_if_not_self)
):
    return {
        "curr_user": curr_user,
        "capability_leader": cl
    }
