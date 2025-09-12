from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from ..models.models import Employee, DebugExercise, DebugResult, TestAssign, Test
from ..config.database import get_db
from ..services.rbac_service import RBACService
import datetime
import asyncio
from ..Agents.DebugEvalauteAgent import evaluate_debug_answers
router = APIRouter(prefix="/debug-test", tags=["debug-test"])

@router.get("/start/{debug_test_id}")
def start_debug_test(
    debug_test_id: int,
    db: Session = Depends(get_db),
    user=Depends(RBACService.get_current_user)
):
    employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    assignment = db.query(TestAssign).join(Test).filter(
        TestAssign.user_id == employee.user_id,
        Test.debug_test_id == debug_test_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Debug test not assigned to employee")
    debug_test = db.query(DebugExercise).filter(DebugExercise.id == debug_test_id).first()
    if not debug_test:
        raise HTTPException(status_code=404, detail="Debug exercise not found")

    duration_sec = debug_test.duration * 60  # Assuming duration in minutes
    minutes = duration_sec // 60
    seconds = duration_sec % 60
    formatted_duration = f"{minutes}:{seconds:02d}"

    # Remove solution/hints/explanation fields
    exer_no_sol = []
    for ex in debug_test.exercises.get("exercises", []):
        ex_copy = ex.copy()
        for field in ["hints", "solution", "explanation"]:
            ex_copy.pop(field, None)
        exer_no_sol.append(ex_copy)

    return {
        "debug_test_id": debug_test.id,
        "test_name": f"Debug Test {debug_test.id}",
        "test_duration": formatted_duration,
        "exercises": exer_no_sol,
    }

@router.post("/submit")
def submit_debug_test(
    submission: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(RBACService.get_current_user)
):
    employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    debug_test_id = submission.get("debug_test_id")
    answers = submission.get("answers")
    start_time = submission.get("start_time")
    debug_test = db.query(DebugExercise).filter(DebugExercise.id == debug_test_id).first()
    if not debug_test:
        raise HTTPException(status_code=404, detail="Debug test not found")

    submitted_at = datetime.datetime.utcnow()
    result = DebugResult(
        user_id=employee.user_id,
        debug_id=debug_test_id,
        score=0,
        answers=answers,
        start_time=start_time,
        submitted_at=submitted_at,
        feedback_data=None
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    background_tasks.add_task(process_debug_feedback, db, result.result_id)
    return {"result_id": result.result_id, "status": "submitted"}

def process_debug_feedback(db, result_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    result = db.query(DebugResult).filter(DebugResult.result_id == result_id).first()
    if not result:
        return

    debug_test = db.query(DebugExercise).filter(DebugExercise.id == result.debug_id).first()
    if not debug_test:
        return

    exercises_data = debug_test.exercises
    user_answers = result.answers

    evaluation = loop.run_until_complete(evaluate_debug_answers(exercises_data, user_answers))
    result.feedback_data = evaluation
    result.score = int(round(evaluation.get("overall_score", 0)))
    db.add(result)
    db.commit()
    loop.close()

@router.get("/score/{debug_test_id}")
def get_debug_score(
    debug_test_id: int,
    db: Session = Depends(get_db),
    user=Depends(RBACService.get_current_user)
):
    employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    result = db.query(DebugResult).filter(
        DebugResult.user_id == employee.user_id,
        DebugResult.debug_id == debug_test_id
    ).order_by(DebugResult.result_id.desc()).first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return result.feedback_data if result.feedback_data else {"pending": True}
