import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
 
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.models import (
    StatusType, TestAssign, Test, Employee, Quiz, QuizResult, DebugExercise, DebugResult
)
from ..services.rbac_service import RBACService
from ..config.database import get_db
from pydantic import BaseModel
from typing import Dict, Any, Optional
import pytz
 
router = APIRouter(prefix="/employee-dashboard", tags=["employee-dashboard"])
 
class TestOut(BaseModel):
    test_id: int
    test_name: str
    test_duration: str
    attempted: bool
    quiz_id: Optional[int] = None
    quiz_name: Optional[str] = None
    quiz_duration: Optional[str] = None
    quiz_attempted: Optional[bool] = None
    debug_test_id: Optional[int] = None
    debug_duration: Optional[str] = None
    debug_attempted: Optional[bool] = False

class AssingedTest(BaseModel):
    test_id: int
    test_name: str
    due_date : datetime.datetime
    debug_url : str
    handson_url : str
    attempted: bool
    quiz_id: Optional[int] = None
    quiz_name: Optional[str] = None
    quiz_duration: Optional[str] = None
    quiz_attempted: Optional[bool] = None

class TestStartOut(BaseModel):
    test_id: int
    test_name: str
    test_duration: str
    test_data: Dict[str, Any]
    created_by:int
 
class SubmitResultIn(BaseModel):
    test_id: int
    answers: Dict[str, str]
    start_time: datetime.datetime
 
@router.get("/assigned-tests", response_model=list[AssingedTest])
def get_assigned_tests(
    db: Session = Depends(get_db),
    user=Depends(RBACService.get_current_user)
):
    employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    assignments = db.query(TestAssign).filter(TestAssign.user_id == employee.user_id).all()
    tests = []
    for assignment in assignments:

        # Quiz details
        test = db.query(Test).filter(Test.id == assignment.test_id).first()
        quiz_id = test.quiz_id

        quiz_name = None
        quiz_duration_str = None
        quiz_attempted = None
        attempted = False
        if quiz_id:
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                quiz_name = quiz.name if hasattr(quiz, "name") else None
                quiz_duration_str = f"{quiz.duration}:00"
            result = db.query(QuizResult).filter(
                QuizResult.user_id == employee.user_id,
                QuizResult.quiz_id == quiz_id
            ).first()
            attempted = result is not None
            quiz_attempted = attempted

        tests.append(
            AssingedTest(
                test_id=assignment.test_id,
                test_name=test.test_name,
                due_date = assignment.due_date,
                debug_url = assignment.debug_github_url or "",
                handson_url = assignment.handson_github_url or "",
                attempted=attempted,

                quiz_id=quiz_id,
                quiz_name=quiz_name,
                quiz_duration=quiz_duration_str,
                quiz_attempted=quiz_attempted,
            )
        )
    return tests
 
@router.get("/start-test/{test_id}", response_model=TestStartOut)
def start_test(
    test_id: int,
    db: Session = Depends(get_db),
    user=Depends(RBACService.get_current_user)
):
    employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    assignment = db.query(TestAssign).filter(
        # TestAssign.user_id == employee.user_id,
        TestAssign.test_id == test_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Test not assigned to employee")
    test = assignment.test
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
 
    # Fetch test data (from quizzes if quiz_id is present)
    test_data = {}
    quiz_duration = None
    if test.quiz_id:
        quiz = db.query(Quiz).filter(Quiz.id == test.quiz_id).first()
        if quiz:
            quiz_duration = quiz.duration*60  # duration in seconds
            # Ensure each question has an 'options' array for MCQs
            test_data = {}
            for qid, qdata in quiz.questions[0].items():
                # If options already exist, use them; else, create MCQ options from correct answer and distractors
                options = qdata.get("options")
                if not options:
                    correct = qdata.get("correctAnswer", "")
                    # Example distractors for Python MCQ
                    distractors = []
                    if "class" in qdata.get("question", "").lower():
                        distractors = [
                            "A variable",
                            "A function",
                            "A module"
                        ]
                    elif "REST" in qdata.get("question", "").lower():
                        distractors = [
                            "Random Event Source Table",
                            "Remote Execution Service",
                            "Relational Entity Set Type"
                        ]
                    # Ensure correct answer is included and options are shuffled
                    options = [correct] + distractors
                # Set type to 'multiple_choice' if options exist
                qtype = "multiple_choice" if options else "text"
                test_data[qid] = {
                    **qdata,
                    "options": options,
                    "type": qtype
                }
 
    # Format duration as MM:SS
    duration_sec = quiz_duration if quiz_duration is not None else test.duration
    minutes = duration_sec // 60
    seconds = duration_sec % 60
    formatted_duration = f"{minutes}:{seconds:02d}"
    
    print(test.created_by,"crea")
    return {
        "test_id": test.id,
        "test_name": test.test_name,
        "test_duration": formatted_duration,
        "test_data": test_data,
        "created_by" : test.created_by
    }
 
@router.post("/submit-test", status_code=201)
def submit_test(
    submission: SubmitResultIn,
    db: Session = Depends(get_db),
    user=Depends(RBACService.get_current_user)
):
    employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    assignment = db.query(TestAssign).filter(
        TestAssign.user_id == employee.user_id,
        TestAssign.test_id == submission.test_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Test not assigned to employee")
    test = assignment.test
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
 
    # Timer enforcement
    quiz_duration = None
    if test.quiz_id:
        quiz = db.query(Quiz).filter(Quiz.id == test.quiz_id).first()
        if quiz:
            quiz_duration = quiz.duration  # duration in seconds
 
    # Timer enforcement removed (no TestSession tracking)
 
    # Scoring logic (for quizzes)
    correct_answers = {}
    if test.quiz_id:
        quiz = db.query(Quiz).filter(Quiz.id == test.quiz_id).first()
        if quiz:
            correct_answers = {q: v["correctAnswer"] for q, v in quiz.questions[0].items()}
    score = sum(
        1 for q, ans in submission.answers.items()
        if correct_answers.get(q) == ans
    )
    total_questions = len(correct_answers)
 
    # Store result (in quiz_results)
   
    local_tz = pytz.timezone("Asia/Calcutta")
    # Convert UTC start_time to local time
    if submission.start_time.tzinfo is None:
        utc_dt = submission.start_time.replace(tzinfo=pytz.utc)
    else:
        utc_dt = submission.start_time.astimezone(pytz.utc)
    local_start_time = utc_dt.astimezone(local_tz).replace(tzinfo=None)
 
    new_result = QuizResult(
        user_id=employee.user_id,
        quiz_id=test.quiz_id,
        score=score,
        start_time=local_start_time,
        submitted_at=datetime.datetime.now(),
        answers=submission.answers
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    # Update assignment status to completed
    assignment.status = StatusType.completed
    db.commit()

    return {
        "result_id": new_result.result_id,
        "status": "submitted",
        "score": score,
        "total": total_questions
    }
 
@router.get("/score/{test_id}")
def get_score(
    test_id: int,
    db: Session = Depends(get_db),
    user=Depends(RBACService.get_current_user)
):
    print("Called")
    employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    test = db.query(Test).filter(Test.id == test_id).first()
    print("1",test)
    if not test or not test.quiz_id:
        raise HTTPException(status_code=404, detail="Test or quiz not found")
    quiz_duration = None
    print(test,"S")
    if test.quiz_id:
        quiz = db.query(Quiz).filter(Quiz.id == test.quiz_id).first()
        if quiz:
            quiz_duration = quiz.duration  # duration in seconds
    result = db.query(QuizResult).filter(
        # QuizResult.user_id == employee.user_id,
        QuizResult.quiz_id == test.quiz_id
    ).order_by(QuizResult.result_id.desc()).first()
    print("qw")
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    # Format duration as MM:SS
    minutes = quiz_duration // 60 if quiz_duration else 0
    seconds = quiz_duration % 60 if quiz_duration else 0
    formatted_duration = f"{minutes}:{seconds:02d}"
 
    return {
        "score": result.score,
        "answers": result.answers,
        "submitted_at": result.submitted_at,
        "duration": formatted_duration,
        "result_id": result.result_id
    }
 
# --- Feedback Agent Integration ---
from ..utils.email import send_feedback_email

@router.get("/feedback/{result_id}")
async def get_feedback_for_result(
    result_id: int,
    db: Session = Depends(get_db),
    user=Depends(RBACService.get_current_user)
):
    from ..Agents.FeedbackAgent.FeedbackAgent import generate_feedback
    import json

    employee = db.query(Employee).filter(Employee.email == user["sub"]).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    result = db.query(QuizResult).filter(
        QuizResult.result_id == result_id,
        # QuizResult.user_id == employee.user_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # If feedback_data already exists, return it directly
    if result.feedback_data:
        return result.feedback_data

    quiz = db.query(Quiz).filter(Quiz.id == result.quiz_id).first()
    questions = quiz.questions if quiz else {}

    quiz_data = {
        "score": result.score,
        "answers": result.answers,
        "questions": questions,
        "submitted_at": str(result.submitted_at),
        "start_time": str(result.start_time),
        "quiz_id": result.quiz_id,
        "user_id": result.user_id
    }
    quiz_data_str = json.dumps(quiz_data)

    feedback_json = await generate_feedback(quiz_data_str)

    # Store feedback in QuizResult
    result.feedback_data = json.loads(feedback_json)
    db.commit()

    send_feedback_email(db, result.user_id, result.quiz_id)

    return json.loads(feedback_json)
