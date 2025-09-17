from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..models.models import DebugExercise, DebugResult

router = APIRouter()

@router.get("/debug/{debug_id}")
def get_user_feedback(
        debug_id: int, user_id: int,
        db: Session = Depends(get_db)
):
    try:
        debug = db.query(DebugResult).filter(
            DebugResult.debug_id == debug_id,
            DebugResult.user_id == user_id
        ).first()
        return debug.feedback_data

    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(500, detail="Something wnet wrong")
