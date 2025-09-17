from datetime import datetime, timedelta
from typing import Optional, Any, Coroutine

from ..schemas.test_schema import AssignTestRequest
from ..services.test_assign import assign_test
from ..models.models import Test
from ..AgentEndpoints.DebugGenAuto import run_debug_gen_auto
from ..Agents.MCQGenSystem import generate_mcq_questions
from sqlalchemy.orm import Session
from ..models.models import TechStack, Topic, Quiz, DebugExercise, Test


async def create_skill_upgrade_test(db: Session, tech_stack_name: str, user_id: int, level: str) -> Test:
    try:
        tech_stack = db.query(TechStack).filter(TechStack.name == tech_stack_name).first()
        if tech_stack is None:
            raise Exception(f"TechStack not found: {tech_stack_name}")

        MAP_DIFFICULTY_LEVEL = {
            "beginner": ['beginner'],
            "intermediate": ['intermediate', 'beginner'],
            "advanced": ['intermediate', 'advanced']
        }
        topics = db.query(Topic).filter(Topic.tech_stack_id == tech_stack.id).all()
        topics_str = ','.join([t.name for t in topics if t.difficulty.value in MAP_DIFFICULTY_LEVEL[level]])
        mcq_json = await generate_mcq_questions(tech_stack=tech_stack.name, topics=topics_str, level=level)
        if not mcq_json:
            raise Exception(f"No MCQ questions created: {tech_stack.name}")
        # Use agent-based debug exercise generation from DebugGenAuto
        await run_debug_gen_auto(
            db=db,
            tech_stack=tech_stack.name,
            topics=topics_str.split(),
            difficulty=level,
            duration=5
        )
        topics_ids = [t.topic_id for t in topics]

        mcq = Quiz(
            tech_stack_id=tech_stack.id,
            topic_ids=topics_ids,
            questions=mcq_json,
            num_questions=20,
            duration=15
        )
        db.add(mcq)

        # Retrieve the latest debug exercise created for this tech_stack and topics
        exercise = db.query(DebugExercise).filter(
            DebugExercise.tech_stack_id == tech_stack.id
        ).order_by(DebugExercise.id.desc()).first()
        if not exercise:
            raise Exception(f"No debug exercises created: {tech_stack.name}")

        db.flush()  # Ensures mcq.id and exercise.id are populated

        test = Test(
            created_by=user_id,
            test_name=f'Skill Upgrade Test {user_id}: {tech_stack.name}: level {level}',
            quiz_id=mcq.id,
            debug_test_id=exercise.id,
            duration=35,
            description=f'Skill Upgrade Test {user_id} of level {level} for {tech_stack.name}'
        )
        db.add(test)
        db.flush()
        db.refresh(test)

        # Assign test and trigger repo creation, file upload, and email notification
        assign_test(
            db=db,
            request=AssignTestRequest(
                user_ids=[user_id],
                test_id=test.id,
                due_date=(datetime.now() + timedelta(days=2)).date()
            ),
            assigned_by=user_id
        )

        return test

    except Exception as e:
        db.rollback()
        print(e)
        raise Exception(f"Failed to create skill upgrade test: {e}")
