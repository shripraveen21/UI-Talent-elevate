from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..models.models import DebugExercise, DebugResult, HandsOnResult, HandsOn

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
        raise HTTPException(500, detail="Something went wrong")


@router.get("/handson/{handson_id}")
def get_user_feedback_handson(
        handson_id: int, user_id: int,
        db: Session = Depends(get_db)
):
    try:
        handson = db.query(HandsOnResult).filter(
            HandsOnResult.handson_id == handson_id,
            HandsOnResult.user_id == user_id
        ).first()
        return handson.feedback_data
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(500, detail="Something went wrong")
