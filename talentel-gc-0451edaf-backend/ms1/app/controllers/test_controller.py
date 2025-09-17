from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..schemas.test_schema import TestCreate, TestOut
from ..services.test_service import create_test, update_test
from ..services.rbac_service import require_roles,RBACService
from ..models.models import RoleEnum,Employee, Collaborator, Test
from ..config.database import get_db
from sqlalchemy import text

router = APIRouter(tags=["tests"])
bearer_scheme = HTTPBearer()

def require_test_permission(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    permission_field: str = "test_create"
):
    """
    Checks if the user has permission to perform test actions.
    - CapabilityLeader and ProductManager have default access.
    - Other users must have the relevant permission in the Collaborator table.
    """
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
    if collab and getattr(collab, permission_field, False):
        return payload

    raise HTTPException(
        status_code=403,
        detail=f"No permission to {permission_field.replace('_', ' ')}"
    )

@router.post("/tests/")
def create_test_endpoint(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    user_payload=Depends(
        lambda db=Depends(get_db), credentials=Depends(bearer_scheme):
            require_test_permission(db, credentials, "test_create")
    )
):
    return create_test(db, user_payload, test_data)

@router.put("/tests/{test_id}/", response_model=TestOut)
def update_test_endpoint(
    test_id: int,
    test_data: TestCreate,
    db: Session = Depends(get_db),
    user_payload=Depends(
        lambda db=Depends(get_db), credentials=Depends(bearer_scheme):
            require_test_permission(db, credentials, "test_assign")
    )
):
    return update_test(db, test_id, user_payload, test_data)

@router.get("/tests/createdBySelf")
def get_tests_created_by_self(db: Session = Depends(get_db), user_payload=Depends(RBACService.get_current_user)):
    """
    Returns tests created by the current user.
    """
    # email = user_payload["sub"]
    # print(email,"Dsaasf")
    print(user_payload,"adsfd")
    user = db.query(Employee).filter(Employee.email == user_payload.get('sub')).first()
    user_id = user.user_id
    tests = db.execute(
        text("""
        SELECT id, test_name, description, duration, created_at, status
        FROM tests
        WHERE created_by = :user_id
        """),
        {"user_id": user.user_id}
    ).fetchall()
    return {"tests": [dict(row._mapping) for row in tests]}

@router.get("/tests/{test_id}/attempts")
def get_test_attempts(test_id: int, db: Session = Depends(get_db)):
    """
    Returns employees who have attempted the given test and their scores.
    Supports both quiz and debug tests.
    """
    # Try to find quiz attempts
    test = db.execute(
        text("""
        SELECT id, quiz_id, debug_test_id
        FROM tests
        WHERE id = :test_id
        """),
        {"test_id": test_id}
    ).fetchall()
    print(test)

    quiz_results = db.execute(
        text("""
        SELECT qr.result_id,e.user_id, e.name, qr.score, qr.quiz_id as test_id
        FROM employees e
        JOIN quiz_results qr ON e.user_id = qr.user_id
        WHERE qr.quiz_id = :test_id
        """),
        {"test_id": test[0][1]}
    ).fetchall()

    # Try to find debug attempts
    debug_results = db.execute(
        text("""
        SELECT dr.result_id,e.user_id, e.name, dr.score, dr.debug_id as test_id
        FROM employees e
        JOIN debug_results dr ON e.user_id = dr.user_id
        WHERE dr.debug_id = :test_id
        """),
        {"test_id": test[0][2]}
    ).fetchall()

    user_attempts = {}

    # Process quiz results
    for row in quiz_results:
        user_attempts[row.user_id] = {
            "user_id": row.user_id,
            "name": row.name,
            "test_id":row.result_id,
            "quiz_marks": row.score,
            "quiz_id": row.test_id,
            "debug_marks": None,
            "debug_id": None
        }

    # Process debug results
    for row in debug_results:
        if row.user_id in user_attempts:
            user_attempts[row.user_id]["debug_marks"] = row.score
            user_attempts[row.user_id]["debug_id"] = row.test_id
        else:
            user_attempts[row.user_id] = {
                "user_id": row.user_id,
                "name": row.name,
                "test_id":row.result_id,
                "quiz_marks": None,
                "quiz_id": None,
                "debug_marks": row.score,
                "debug_id": row.test_id
            }

    # Convert to list
    attempts = list(user_attempts.values())
    print(attempts,"att")
    return {"attempts": attempts}

    # # Combine results
    # attempts = []
    # for row in quiz_results:
    #     attempts.append({"user_id": row.user_id, "name": row.name, "score": row.score,"test_id":row.test_id,"quiz":True})
    # for row in debug_results:
    #     attempts.append({"user_id": row.user_id, "name": row.name, "score": row.score,"test_id":row.test_id,"quiz":False})
    
    # print("atemps",attempts,test_id)
    # return {"attempts": attempts}
