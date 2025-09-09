from sqlalchemy import or_
from ..models.models import Employee, Test, TestAssign
from ..schemas.test_schema import AssignTestRequest, TestFilter,TestOut
from sqlalchemy.orm import Session

def list_tests(db: Session, filters: TestFilter):
    query = db.query(Test)
    if filters.created_from:
        query = query.filter(Test.created_at >= filters.created_from)
    if filters.created_to:
        query = query.filter(Test.created_at <= filters.created_to)
    if filters.search:
        search = f"%{filters.search}%"
        query = query.filter(Test.test_name.ilike(search))
    total = query.count()
    tests = query.offset((filters.page-1)*filters.page_size).limit(filters.page_size).all()
    return total, tests

from ..utils.email import send_assignment_email

def assign_test(db: Session, request: AssignTestRequest):
    assignments = []
    for user_id in request.user_ids:
        assignment = TestAssign(
            user_id=user_id,
            test_id=request.test_id,
            status="assigned",
            due_date=request.due_date,
            mail_sent="Not_sent"
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Send assignment email using the new utility
        email_sent = send_assignment_email(db, user_id, request.test_id, request.due_date)
        assignment.mail_sent = "Sent" if email_sent else "Failed"
        db.commit()
        db.refresh(assignment)
        assignments.append(assignment)
    return assignments
