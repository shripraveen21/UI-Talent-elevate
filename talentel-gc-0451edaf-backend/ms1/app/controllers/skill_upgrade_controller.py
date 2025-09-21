import asyncio

from ..config.database import get_db
from ..services.skill_upgrade_service import *
from ..services.rbac_service import RBACService
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from ..models.models import Employee, EmployeeSkill, SkillUpgrade, TestAssign, Test, QuizResult, DebugResult, HandsOnResult, DifficultyLevel
from ..schemas.test_schema import TestOut, SkillUpgradeRequest
from fastapi import Request

router = APIRouter()

@router.post('/skill-upgrade')
async def skill_upgrade(
    request: SkillUpgradeRequest,
    db: Session = Depends(get_db),
    curr_user = Depends(RBACService.get_current_user),
    background_tasks: BackgroundTasks = None
):
    try:
        user = db.query(Employee).filter(Employee.email == curr_user.get('sub')).first()
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")
        tech_stack_db = db.query(TechStack).filter(TechStack.name == request.tech_stack).first()
        if not tech_stack_db:
            raise HTTPException(status_code=404, detail="Tech stack not found")

        test = asyncio.create_task(create_skill_upgrade_test(
            db=db, tech_stack_name=request.tech_stack,
            user_id=user.user_id, level=request.level,
            background_tasks=background_tasks
        ))
        # Convert SQLAlchemy model to Pydantic schema
        return {"status": "Generating"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/skill-upgrade/complete')
async def complete_skill_upgrade(
    test_id: int,
    db: Session = Depends(get_db),
    curr_user=Depends(RBACService.get_current_user)
):
    try:
        import logging
        logger = logging.getLogger("skill_upgrade_complete")

        user = db.query(Employee).filter(Employee.email == curr_user.get('sub')).first()
        if not user:
            logger.error("Employee not found for email: %s", curr_user.get('sub'))
            raise HTTPException(status_code=404, detail="Employee not found")

        test_assign = db.query(TestAssign).filter(
            TestAssign.user_id == user.user_id,
            TestAssign.test_id == test_id
        ).first()
        if not test_assign:
            logger.error("Test assignment not found for user_id: %s, test_id: %s", user.user_id, test_id)
            raise HTTPException(status_code=404, detail="Test assignment not found for user")

        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            logger.error("Test not found for test_id: %s", test_id)
            raise HTTPException(status_code=404, detail="Test not found")

        quiz_id = test.quiz_id
        debug_id = test.debug_test_id
        handson_id = test.handson_id

        quiz_score = None
        debug_score = None
        handson_score = None

        if quiz_id:
            quiz_result = db.query(QuizResult).filter(
                QuizResult.user_id == user.user_id,
                QuizResult.quiz_id == quiz_id
            ).order_by(QuizResult.submitted_at.desc()).first()
            if quiz_result:
                quiz_score = quiz_result.score

        if debug_id:
            debug_result = db.query(DebugResult).filter(
                DebugResult.user_id == user.user_id,
                DebugResult.debug_id == debug_id
            ).order_by(DebugResult.result_id.desc()).first()
            if debug_result:
                debug_score = debug_result.score

        if handson_id:
            handson_result = db.query(HandsOnResult).filter(
                HandsOnResult.user_id == user.user_id,
                HandsOnResult.handson_id == handson_id
            ).order_by(HandsOnResult.result_id.desc()).first()
            if handson_result:
                handson_score = handson_result.score

        if quiz_score is None or debug_score is None or handson_score is None:
            logger.error(
                "Missing scores: quiz_score=%s, debug_score=%s, handson_score=%s",
                quiz_score, debug_score, handson_score
            )
            raise HTTPException(status_code=400, detail="One or more results not published yet")

        total_score = quiz_score * 5 + debug_score + handson_score
        final_score = total_score / 3

        skill_upgrade = db.query(SkillUpgrade).filter(
            SkillUpgrade.employee_id == user.user_id,
            SkillUpgrade.assigned_test_id == test_id
        ).first()
        tech_stack_id = skill_upgrade.tech_stack_id if skill_upgrade else None
        target_level = skill_upgrade.target_level if skill_upgrade else None
        if not tech_stack_id:
            logger.error("Tech stack ID not found in SkillUpgrade for employee_id: %s, test_id: %s", user.user_id, test_id)
            raise HTTPException(status_code=400, detail="Tech stack ID not found for test")
        if not target_level:
            logger.error("Target level not found in SkillUpgrade for employee_id: %s, test_id: %s", user.user_id, test_id)
            raise HTTPException(status_code=400, detail="Target level not found for skill upgrade")

        if final_score >= 80:
            emp_skill = db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id == user.user_id,
                EmployeeSkill.tech_stack_id == tech_stack_id
            ).first()
            if emp_skill:
                emp_skill.current_level = target_level
            else:
                emp_skill = EmployeeSkill(
                    employee_id=user.user_id,
                    tech_stack_id=tech_stack_id,
                    current_level=target_level
                )
                db.add(emp_skill)
            db.commit()
            return {
                "success": True,
                "message": "Skill upgrade completed and added to profile.",
                "final_score": final_score,
                "employee_id": user.user_id,
                "tech_stack_id": tech_stack_id,
                "current_level": target_level.value if hasattr(target_level, "value") else str(target_level)
            }
        else:
            return {
                "success": False,
                "message": "Final score below 80. Skill upgrade not added.",
                "final_score": final_score
            }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/get-skills')
async def get_curr_user_skills(
        db: Session = Depends(get_db),
        curr_user=Depends(RBACService.get_current_user)
):
    try:
        user = db.query(Employee).filter(Employee.email == curr_user.get('sub')).first()
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")
        user_skills = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == user.user_id
        )
        ts_ids = [s.tech_stack_id for s in user_skills]
        tech_stacks = db.query(TechStack).filter(
            TechStack.id.in_(ts_ids)
        ).all()
        result = [
            {
                "tech_stack_id": ts.id,
                "name": ts.name,
            }
            for ts in tech_stacks
        ]
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
