from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services.rbac_service import RBACService
from ..models.models import Employee, Collaborator, RoleEnum
from ..schemas.employee_schema import EmployeeFilter, EmployeeOut
from ..config.database import get_db
from ..services.employee_service import list_employees as list_employees_service, get_employee_tech_stack

router = APIRouter()
bearer_scheme = HTTPBearer()

def require_employee_permission(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    payload = RBACService.get_current_user(credentials)
    email = payload.get("sub")
    role = payload.get("role")

    # Use .value for all enums
    if role in [
        RoleEnum.CapabilityLeader.value,
        RoleEnum.ProductManager.value,
        RoleEnum.DeliveryLeader.value,
        RoleEnum.DeliveryManager.value
    ]:
        return payload

    user = db.query(Employee).filter(Employee.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    collab = db.query(Collaborator).filter(Collaborator.collaborator_id == user.user_id).first()
    if collab and getattr(collab, "test_assign", False):
        return payload

    raise HTTPException(
        status_code=403,
        detail="No permission to manage employees"
    )

@router.post("/employees", response_model=dict)
def list_employees(
    filters: EmployeeFilter = None,
    db: Session = Depends(get_db),
    user_payload = Depends(require_employee_permission)
):
    if filters is None:
        filters = EmployeeFilter()
    total, employees = list_employees_service(db=db, filters=filters)
    return {
        "total": total,
        "employees": [EmployeeOut.from_orm(emp) for emp in employees]
    }

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
    user_payload = Depends(require_employee_permission)
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
    employee_list = []
    for emp in employees:
        emp_out = EmployeeOut.from_orm(emp).dict()
        tech_stack_data = get_employee_tech_stack(db, emp.user_id)
        if tech_stack_data and len(tech_stack_data) > 0:
            emp_out["tech_stack"] = tech_stack_data
        elif emp.tech_stack and isinstance(emp.tech_stack, dict) and len(emp.tech_stack) > 0:
            emp_out["tech_stack"] = emp.tech_stack
        else:
            emp_out["tech_stack"] = None
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

@router.get("/employee-filter-options", response_model=dict)
def get_employee_filter_options(
    db: Session = Depends(get_db),
    user_payload = Depends(require_employee_permission)
):
    from ..models.models import BandType, RoleEnum, SkillLevel
    return {
        "bands": [b.value for b in BandType],
        "roles": [r.value for r in RoleEnum],
        "skill_levels": [s.value for s in SkillLevel]
    }
