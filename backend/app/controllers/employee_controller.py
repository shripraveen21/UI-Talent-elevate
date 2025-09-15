from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..services.rbac_service import require_roles
from ..schemas.employee_schema import EmployeeFilter, EmployeeOut
from ..config.database import get_db
from ..models.models import RoleEnum
from ..services.employee_service import list_employees as list_employees_service, get_employee_tech_stack

router = APIRouter()

@router.post("/employees", response_model=dict)
def list_employees(
    filters: EmployeeFilter = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(RoleEnum.CapabilityLeader,RoleEnum.ProductManager))
):
    # If no filters provided, use default EmployeeFilter
    if filters is None:
        filters = EmployeeFilter()
    total, employees = list_employees_service(db=db, filters=filters)
    return {
        "total": total,
        "employees": [EmployeeOut.from_orm(emp) for emp in employees]
    }

from fastapi import Query

@router.get("/employees", response_model=dict)
def list_employees_get(
    band: str = Query(None),
    skills: str = Query(None, description="Comma-separated list of skills"),
    designation: str = Query(None),
    skill_name: str = Query(None, description="Skill name to filter by level, e.g. 'python'"),
    skill_level: str = Query(None, description="Skill level to filter, e.g. 'Trained'"),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(RoleEnum.CapabilityLeader,RoleEnum.ProductManager))
):
    total, employees = list_employees_service(
        db=db,
        band=band,
        skills=skills,
        designation=designation,
        skill_name=skill_name,
        skill_level=skill_level,
        search=search,
        page=page,
        page_size=page_size
    )
    # Include full tech_stack and python skill_level in response
    employee_list = []
    for emp in employees:
        emp_out = EmployeeOut.from_orm(emp).dict()
        
        # Get tech stack data from EmployeeSkill table
        tech_stack_data = get_employee_tech_stack(db, emp.user_id)
        
        # Set tech_stack data - use EmployeeSkill table data if available, otherwise fallback to JSON column
        if tech_stack_data and len(tech_stack_data) > 0:
            emp_out["tech_stack"] = tech_stack_data
        elif emp.tech_stack and isinstance(emp.tech_stack, dict) and len(emp.tech_stack) > 0:
            emp_out["tech_stack"] = emp.tech_stack
        else:
            emp_out["tech_stack"] = None  # Set to None if no data available
        
        # Also include python skill_level for backward compatibility
        python_level = None
        if tech_stack_data:
            python_level = tech_stack_data.get("python")
        elif emp.tech_stack and isinstance(emp.tech_stack, dict):
            python_level = emp.tech_stack.get("python")
        emp_out["python_skill_level"] = python_level
        employee_list.append(emp_out)
    return {
        "total": total,
        "employees": employee_list
    }

from ..models.models import BandType, RoleEnum, SkillLevel
from fastapi import APIRouter

@router.get("/employee-filter-options", response_model=dict)
def get_employee_filter_options():
    return {
        "bands": [b.value for b in BandType],
        "roles": [r.value for r in RoleEnum],
        "skill_levels": [s.value for s in SkillLevel]
    }
