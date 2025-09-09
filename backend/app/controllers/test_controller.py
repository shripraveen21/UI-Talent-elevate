from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..schemas.test_schema import TestCreate, TestOut
from ..services.test_service import create_test, update_test
from ..services.rbac_service import require_roles
from ..models.models import RoleEnum
from ..config.database import get_db

router = APIRouter(tags=["tests"])

@router.post("/tests/", response_model=TestOut)
def create_test_endpoint(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    user_payload=Depends(require_roles(RoleEnum.CapabilityLeader, RoleEnum.ProductManager))
):
    return create_test(db, user_payload, test_data)

@router.put("/tests/{test_id}/", response_model=TestOut)
def update_test_endpoint(
    test_id: int,
    test_data: TestCreate,
    db: Session = Depends(get_db),
    user_payload=Depends(require_roles(RoleEnum.CapabilityLeader, RoleEnum.ProductManager))
):
    return update_test(db, test_id, user_payload, test_data)
