from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..schemas.employee_schema import EmployeeFilter, EmployeeOut
from ..models.models import Employee, EmployeeSkill, TechStack

from sqlalchemy import and_, cast
from sqlalchemy.dialects.postgresql import JSONB

def list_employees(
    db: Session,
    band=None,
    skills=None,
    designation=None,
    skill_name=None,
    skill_level=None,
    search=None,
    page=1,
    page_size=10,
    
):
    query = db.query(Employee)
    from ..models.models import BandType
    valid_bands = {b.value for b in BandType}
    if band and band != "string" and band in valid_bands:
        query = query.filter(Employee.band == band)
    if designation and designation != "string":
        query = query.filter(Employee.role == designation)
    if skills:
        # skills is a comma-separated string
        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
        from sqlalchemy import Text
        for skill in skill_list:
            # Fallback: string search for key in JSON (works for JSON column)
            query = query.filter(Employee.tech_stack.cast(Text).ilike(f'%"{skill}":%'))
    if skill_name and skill_level:
        # Filter where tech_stack->>skill_name == skill_level (Postgres JSON column)
        query = query.filter(Employee.tech_stack.op('->>')(skill_name) == skill_level)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(or_(Employee.name.ilike(search_pattern), Employee.email.ilike(search_pattern)))
    total = query.count()
    employees = query.offset((page-1)*page_size).limit(page_size).all()
    return total, employees

def get_employee_tech_stack(db: Session, employee_id: int) -> dict:
    """
    Get employee's tech stack data from EmployeeSkill table
    Returns a dictionary with tech stack names as keys and skill levels as values
    """
    employee_skills = db.query(EmployeeSkill, TechStack).join(
        TechStack, EmployeeSkill.tech_stack_id == TechStack.id
    ).filter(EmployeeSkill.employee_id == employee_id).all()
    
    tech_stack_dict = {}
    for emp_skill, tech_stack in employee_skills:
        tech_stack_dict[tech_stack.name.lower()] = emp_skill.current_level.value.lower()
    
    return tech_stack_dict
