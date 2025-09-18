from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..config.database import get_db
from ..models.models import Employee, DebugExercise, DebugResult, HandsOnResult, TestAssign, Test
from ..services.rbac_service import RBACService

router = APIRouter(tags=["hands_on"])

@router.get("/handson-result/{handson_id}")
def get_handson_result(handson_id: int, db: Session = Depends(get_db),user=Depends(RBACService.get_current_user)):
    """
    Returns the hands-on result for a given test_id in the handson.json structure.
    """
    import logging
    try:

        employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        handson_result = db.query(HandsOnResult).filter(
            # DebugResult.user_id == employee.user_id,
            HandsOnResult.handson_id == handson_id
        ).first()
        
       
        print(handson_result,"Result handson")

        logging.info(f"Fetched handson result for test_id={handson_id}")
        return handson_result

    except Exception as e:
        logging.error(f"Error fetching handson result for test_id={handson_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch handson result")
