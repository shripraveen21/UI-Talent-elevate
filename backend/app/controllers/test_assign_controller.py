from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.test_schema import AssignTestRequest, TestFilter, TestOut
from app.services.test_assign import list_tests as list_tests_service, assign_test as assign_test_service
from ..config.database import get_db

router = APIRouter()

@router.get("/tests", response_model=dict)
def list_tests(
    filters: TestFilter = Depends(),
    db: Session = Depends(get_db)
):
    total, tests = list_tests_service(db=db, filters=filters)
    return {
        "total": total,
        "tests": [TestOut.from_orm(test) for test in tests]
    }

@router.post("/assign-test", response_model=dict)
def assign_test(
    request: AssignTestRequest,
    db: Session = Depends(get_db)
):
    try:
        assignments = assign_test_service(db=db, request=request)
        return {
            "message": "Test(s) assigned successfully",
            "assignments": [
                {
                    "assignment_id": a.assign_id,
                    "user_id": a.user_id,
                    "test_id": a.test_id,
                    "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                    "due_date": a.due_date,
                    "mail_sent": a.mail_sent
                }
                for a in assignments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
