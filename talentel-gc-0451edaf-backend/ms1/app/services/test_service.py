from sqlalchemy.orm import Session

from ..schemas.test_schema import TestCreate
# from app.models.models import Test, Quiz, HandsonData, DebugExercise
from ..models.models import Employee, Test, Quiz, DebugExercise
from fastapi import HTTPException

def create_test(db: Session, user_payload, test_data:TestCreate):
    # Ensure test name is unique
    if db.query(Test).filter_by(test_name=test_data.test_name).first():
        raise HTTPException(status_code=400, detail="Test name already exists.")
    
    print(user_payload)
    user = db.query(Employee).filter(Employee.email == user_payload['sub']).first()
    print("user data in service",user)

    test = Test(
        test_name=test_data.test_name,
        description=test_data.description,
        duration=test_data.duration,
        created_by=user.user_id,
        quiz_id=test_data.quiz_id,
        debug_test_id=test_data.debug_test_id
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    db.commit()
    db.refresh(test)
    return test

def update_test(db: Session, test_id: int, user_payload, test_data):
    test = db.query(Test).filter_by(test_id=test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found.")

    # Update main test fields
    test.name = test_data.name
    test.topic_id = test_data.topic_id
    test.difficulty_id = test_data.difficulty_id
    test.test_type = test_data.test_type
    test.title = test_data.title

    # Update or create the relevant data
    if test_data.test_type == "quiz" and test_data.quiz_data:
        quiz_data = db.query(Quiz).filter_by(test_id=test_id).first()
        if quiz_data:
            quiz_data.data = {"questions": [q.dict() for q in test_data.quiz_data.questions]}
        else:
            quiz_data = Quiz(
                test_id=test_id,
                data={"questions": [q.dict() for q in test_data.quiz_data.questions]}
            )
            db.add(quiz_data)
    elif test_data.test_type == "debug" and test_data.debug_data:
        debug_data = db.query(DebugExercise).filter_by(test_id=test_id).first()
        if debug_data:
            debug_data.prompt = test_data.debug_data.prompt
            debug_data.solution = test_data.debug_data.solution
        else:
            debug_data = DebugExercise(
                test_id=test_id,
                prompt=test_data.debug_data.prompt,
                solution=test_data.debug_data.solution
            )
            db.add(debug_data)
    else:
        raise HTTPException(status_code=400, detail="Test data does not match test type.")

    db.commit()
    db.refresh(test)
    return test
