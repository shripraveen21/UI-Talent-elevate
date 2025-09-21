from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..config.database import get_db
from ..models.models import Employee, DebugExercise, DebugResult, HandsOnResult, TestAssign, Test
from ..services.rbac_service import RBACService
import logging
router = APIRouter(tags=["hands_on"])

@router.get("/handson-result/{handson_id}")
def get_handson_result(handson_id: int, db: Session = Depends(get_db),user=Depends(RBACService.get_current_user)):
    """
    Returns the hands-on result for a given test_id in the handson.json structure.
    """
    
    try:
        print(handson_id,"handson result")

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

@router.put("/handson-result/{handson_id}/complete")
def mark_handson_completed(handson_id: int, db: Session = Depends(get_db), user=Depends(RBACService.get_current_user)):
    """
    Marks the hands-on result as completed (is_submitted=True) for the current user and handson_id.
    """
    try:
        employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
        if not employee:
            logging.error(f"Employee not found for email: {user['sub']}")
            raise HTTPException(status_code=404, detail="Employee not found")

        print(handson_id,employee.user_id,"handson compelete")
        handson_result = db.query(HandsOnResult).filter(
            HandsOnResult.user_id == employee.user_id,
            HandsOnResult.handson_id == handson_id
        ).first()

        if not handson_result:
            logging.error(f"HandsOnResult not found for user_id={employee.user_id}, handson_id={handson_id}")
            raise HTTPException(status_code=404, detail="HandsOnResult not found")

        if handson_result.is_submitted:
            logging.info(f"HandsOnResult already marked as completed for user_id={employee.user_id}, handson_id={handson_id}")
            return {"message": "Handson already marked as completed"}

        handson_result.is_submitted = True
        db.commit()
        logging.info(f"Marked handson as completed for user_id={employee.user_id}, handson_id={handson_id}")
        return {"message": "Handson marked as completed"}

    except Exception as e:
        logging.error(f"Error marking handson as completed for handson_id={handson_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark handson as completed")
