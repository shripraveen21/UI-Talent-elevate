from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..schemas.test_schema import AssignTestRequest, TestFilter, TestOut
from ..services.test_assign import list_tests as list_tests_service, assign_test as assign_test_service
from ..config.database import get_db
from ..models.models import Employee, Collaborator, RoleEnum
from ..services.rbac_service import RBACService

router = APIRouter()
bearer_scheme = HTTPBearer()




def require_test_assign_permission(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    payload = RBACService.get_current_user(credentials)
    email = payload.get("sub")
    role = payload.get("role")

    # Default access for CapabilityLeader and ProductManager
    if role in [RoleEnum.CapabilityLeader.value, RoleEnum.ProductManager.value, RoleEnum.DeliveryLeader, RoleEnum.DeliveryManager]:
        return payload

    # For other users, check Collaborator table for permission
    user = db.query(Employee).filter(Employee.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    collab = db.query(Collaborator).filter(Collaborator.collaborator_id == user.user_id).first()
    if collab and getattr(collab, "test_assign", False):
        return payload

    raise HTTPException(
        status_code=403,
        detail="No permission to assign or manage tests"
    )

@router.get("/tests/", response_model=dict)
def list_tests(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    user_payload=Depends(require_test_assign_permission)
):
    filters = {
        "search": "",
        "page": page,
        "page_size": page_size
    }
    total, tests = list_tests_service(db=db, filters=filters)
    return {
        "total": total,
        "tests": [TestOut.from_orm(test) for test in tests]
    }

@router.post("/tests/assign-test", response_model=dict)
def assign_test(
    request: AssignTestRequest,
    db: Session = Depends(get_db),
    user_payload=Depends(require_test_assign_permission)
):
    try:
        email = user_payload["sub"]
        user = db.query(Employee).filter(Employee.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")
        assigned_by = user.user_id

        assignments = assign_test_service(db=db, request=request, assigned_by=assigned_by)
        return {
            "message": "Test(s) assigned successfully",
            "assignments": [
                {
                    "assignment_id": a.assign_id,
                    "user_id": a.user_id,
                    "test_id": a.test_id,
                    "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                    "due_date": a.due_date,
                    "mail_sent": a.mail_sent,
                    "assigned_by": a.assigned_by
                }
                for a in assignments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

