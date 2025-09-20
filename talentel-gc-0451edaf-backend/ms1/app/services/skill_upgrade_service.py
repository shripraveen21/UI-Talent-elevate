from datetime import datetime, timedelta
from typing import Optional, Any, Coroutine

from ..schemas.test_schema import AssignTestRequest
from ..services.test_assign import assign_test
from ..models.models import (
    Test, TechStack, Topic, Quiz, DebugExercise, HandsOn, Employee, EmployeeSkill,
    SkillUpgrade, QuizResult, DebugResult, HandsOnResult, DifficultyLevel
)
from ..AgentEndpoints.DebugGenAuto import run_debug_gen_auto
from ..AgentEndpoints.HandsONGenAuto import run_handson_gen_auto
from ..Agents.MCQGenSystem import generate_mcq_questions
import asyncio
from sqlalchemy.orm import Session

async def create_skill_upgrade_test(db: Session, tech_stack_name: str, user_id: int, level: str, background_tasks=None) -> Test:
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
        # Use agent-based hands-on generation from HandsONGenAuto
        handson_result = await run_handson_gen_auto(
            db=db,
            tech_stack=tech_stack.name if hasattr(tech_stack, "name") else tech_stack,
            topics=[t.name for t in topics if hasattr(t, "name")],
            duration=1
        )
        hands_on_id = handson_result.get("handson_id")
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
            handson_id=hands_on_id,
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

        # Save SkillUpgrade record
        from ..models.models import SkillUpgrade, DifficultyLevel, StatusType
        skill_upgrade = SkillUpgrade(
            employee_id=user_id,
            tech_stack_id=tech_stack.id,
            target_level=DifficultyLevel(level),
            status=StatusType.assigned,
            assigned_test_id=test.id,
            start_time=datetime.now()
        )
        db.add(skill_upgrade)
        db.commit()
        db.refresh(skill_upgrade)

        return test

    except Exception as e:
        db.rollback()
        print(e)
        raise Exception(f"Failed to create skill upgrade test: {e}")

def aggregate_and_update_employee_skills(db: Session):
    """
    For each completed SkillUpgrade, aggregate quiz, debug, and handson scores.
    If all three results exist and average >= 80, add/update EmployeeSkill for tech_stack and target_level.
    """
    skill_upgrades = db.query(SkillUpgrade).filter(SkillUpgrade.status == 'completed').all()
    for upgrade in skill_upgrades:
        employee_id = upgrade.employee_id
        tech_stack_id = upgrade.tech_stack_id
        target_level = upgrade.target_level
        test_id = upgrade.assigned_test_id

        if not test_id:
            continue

        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            continue

        quiz_id = test.quiz_id
        debug_id = test.debug_test_id
        handson_id = test.handson_id

        # Fetch results for this employee and test components
        quiz_result = db.query(QuizResult).filter(
            QuizResult.user_id == employee_id,
            QuizResult.quiz_id == quiz_id
        ).order_by(QuizResult.result_id.desc()).first() if quiz_id else None

        debug_result = db.query(DebugResult).filter(
            DebugResult.user_id == employee_id,
            DebugResult.debug_id == debug_id
        ).order_by(DebugResult.result_id.desc()).first() if debug_id else None

        handson_result = db.query(HandsOnResult).filter(
            HandsOnResult.user_id == employee_id,
            HandsOnResult.handson_id == handson_id
        ).order_by(HandsOnResult.result_id.desc()).first() if handson_id else None

        # Only proceed if all three results exist
        if quiz_result and debug_result and handson_result:
            scores = [quiz_result.score, debug_result.score, handson_result.score]
            avg_score = sum(scores) / len(scores)
            if avg_score >= 80:
                # Add or update EmployeeSkill
                emp_skill = db.query(EmployeeSkill).filter(
                    EmployeeSkill.employee_id == employee_id,
                    EmployeeSkill.tech_stack_id == tech_stack_id
                ).first()
                if emp_skill:
                    emp_skill.current_level = target_level
                else:
                    emp_skill = EmployeeSkill(
                        employee_id=employee_id,
                        tech_stack_id=tech_stack_id,
                        current_level=target_level
                    )
                    db.add(emp_skill)
                db.commit()
