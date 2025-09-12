from datetime import datetime, timedelta
from typing import Optional, Any, Coroutine

from ..schemas.test_schema import AssignTestRequest
from ..services.test_assign import assign_test
from ..models.models import Test
from ..Agents.DebugExerciseSystem import generate_exercises
from ..Agents.MCQGenSystem import generate_mcq_questions
from sqlalchemy.orm import Session
from ..models.models import TechStack, Topic, Quiz, DebugExercise, Test, TestStatus


async def create_skill_upgrade_test(db: Session, tech_stack_name: str, user_id: int, level: str) -> Test:
    try:
        tech_stack = db.query(TechStack).filter(TechStack.name == tech_stack_name).first()
        if tech_stack is None:
            raise Exception(f"TechStack not found: {tech_stack_name}")

        MAP_DIFFICULTY_LEVEL = {
            "TRAINED": ['beginner'],
            "BASIC": ['intermediate', 'beginner'],
            "INTERMEDIATE": ['intermediate'],
            "ADVANCED": ['intermediate', 'advanced'],
            "GURU": ['advanced']
        }
        topics = db.query(Topic).filter(Topic.tech_stack_id == tech_stack.id).all()
        topics_str = ','.join([t.name for t in topics if t.difficulty.value in MAP_DIFFICULTY_LEVEL[level]])
        mcq_json = await generate_mcq_questions(tech_stack=tech_stack.name, topics=topics_str, level=level)
        if not mcq_json:
            raise Exception(f"No MCQ questions created: {tech_stack.name}")
        exercise_json = await generate_exercises(tech_stack=tech_stack.name, topics=topics_str.split(), level=level)
        if not exercise_json:
            raise Exception(f"No exercises created: {tech_stack.name}")
        topics_ids = [t.topic_id for t in topics]

        mcq = Quiz(
            tech_stack_id=tech_stack.id,
            topic_ids=topics_ids,
            questions=mcq_json,
            num_questions=20,
            duration=15
        )
        db.add(mcq)

        exercise = DebugExercise(
            tech_stack_id=tech_stack.id,
            topic_ids=topics_ids,
            num_questions=5,
            duration=15,
            exercises=exercise_json.get('exercises')
        )
        db.add(exercise)

        db.flush()  # Ensures mcq.id and exercise.id are populated

        test = Test(
            created_by=user_id,
            test_name=f'Skill Upgrade Test {user_id}: {tech_stack.name}: level {level}',
            quiz_id=mcq.id,
            debug_test_id=exercise.id,
            status=TestStatus.approved,
            duration=35,
            description=f'Skill Upgrade Test {user_id} of level {level} for {tech_stack.name}'
        )
        db.add(test)
        db.flush()
        db.refresh(test)

        assign_test(
            db=db,
            request=AssignTestRequest(
                user_ids=[user_id],
                test_id=test.id,
                due_date=(datetime.now() + timedelta(days=2)).date(),
            )
        )

        return test

    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to create skill upgrade test: {e}")
