from ..config.database import get_db
from ..services.skill_upgrade_service import *
from ..services.rbac_service import RBACService
from fastapi import APIRouter, Depends, HTTPException
from ..models.models import Employee, EmployeeSkill ,SkillUpgrade
from ..schemas.test_schema import TestOut,SkillUpgradeRequest

router = APIRouter()

@router.post('/skill-upgrade', response_model=TestOut)
async def skill_upgrade(
    request: SkillUpgradeRequest,
    db: Session = Depends(get_db),
    curr_user = Depends(RBACService.get_current_user)
):
    try:
        user = db.query(Employee).filter(Employee.email == curr_user.get('sub')).first()
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")
        tech_stack_db = db.query(TechStack).filter(TechStack.name == request.tech_stack).first()
        if not tech_stack_db:
            raise HTTPException(status_code=404, detail="Tech stack not found")

        test = await create_skill_upgrade_test(
            db=db, tech_stack_name=request.tech_stack,
            user_id=user.user_id, level=request.level
        )
        # Convert SQLAlchemy model to Pydantic schema
        return TestOut.from_orm(test)
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
 