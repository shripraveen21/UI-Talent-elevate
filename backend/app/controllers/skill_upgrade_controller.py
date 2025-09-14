from ..config.database import get_db
from ..services.skill_upgrade_service import *
from ..services.rbac_service import RBACService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.models import Employee, EmployeeSkill, TechStack
from ..schemas.test_schema import TestOut

router = APIRouter()

@router.post('/skill-upgrade', response_model=TestOut)
async def skill_upgrade(
    tech_stack: str,
    db: Session = Depends(get_db),
    curr_user = Depends(RBACService.get_current_user)
):
    try:
        user = db.query(Employee).filter(Employee.email == curr_user.get('sub')).first()
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")
        tech_stack_db = db.query(TechStack).filter(TechStack.name == tech_stack).first()
        if not tech_stack_db:
            raise HTTPException(status_code=404, detail="Tech stack not found")
        user_skill = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == user.user_id,
            EmployeeSkill.tech_stack_id == tech_stack_db.id
        ).first()
        if not user_skill:
            raise HTTPException(status_code=404, detail="User skill for this tech stack not found")
        user_level = user_skill.current_level.value

        test = await create_skill_upgrade_test(
            db=db, tech_stack_name=tech_stack,
            user_id=user.user_id, level=user_level
        )
        # Convert SQLAlchemy model to Pydantic schema
        return TestOut.from_orm(test)

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
