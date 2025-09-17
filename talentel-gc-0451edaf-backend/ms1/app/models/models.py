from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Text, ForeignKey, Enum, UniqueConstraint,
    JSON, ARRAY, CheckConstraint, func, Boolean, UUID
)
 
from sqlalchemy.orm import relationship
from ..config.database import Base
import enum
 
# Enums
class RoleEnum(enum.Enum):
    ProductManager = "ProductManager"
    Employee = "Employee"
    CapabilityLeader = "CapabilityLeader"
    DeliveryManager = "DeliveryManager"
    DeliveryLeader = "DeliveryLeader"
 
class DifficultyLevel(enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
 
class StatusType(enum.Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    canceled = "canceled"
    not_completed = "not_completed"

class BandType(enum.Enum):
    B2 = "B2"
    B3H = "B3H"
    B3L = "B3L"
    B4H = "B4H"
    B4L = "B4L"
    B5H = "B5H"
    B5L = "B5L"
    B6H = "B6H"
    B6L = "B6L"
    B7 = "B7"
    B8 = "B8"
 
class MailStatus(enum.Enum):
    Sent = "Sent"
    Failed = "Failed"
    Not_sent = "Not_sent"

# Models

class Employee(Base):
    __tablename__ = 'employees'
    user_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    band = Column(Enum(BandType), nullable=False)
    tech_stack = Column(JSON)
    manager_id = Column(Integer, ForeignKey('employees.user_id'))
    manager = relationship('Employee', remote_side=[user_id], backref='reports')
 
    skills = relationship('EmployeeSkill', back_populates='employee')
    collaborations = relationship('Collaborator', foreign_keys='Collaborator.cl_id', back_populates='owner')
    collaborated_with = relationship('Collaborator', foreign_keys='Collaborator.collaborator_id',
                                     back_populates='collaborator')

class TechStack(Base):
    __tablename__ = 'tech_stack'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    created_by = Column(Integer, ForeignKey('employees.user_id'))
    created_at = Column(DateTime, default=func.now())
 
    employee_skills = relationship('EmployeeSkill', back_populates='tech_stack')
 
class Topic(Base):
    __tablename__ = 'topics'
    topic_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    difficulty = Column(Enum(DifficultyLevel), nullable=False)
    tech_stack_id = Column(Integer, ForeignKey('tech_stack.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('name', 'tech_stack_id', 'difficulty', name='uniq_topic_per_stack'),
    )
 
class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True)
    tech_stack_id = Column(Integer, ForeignKey('tech_stack.id', ondelete='CASCADE'), nullable=False)
    topic_ids = Column(ARRAY(Integer), nullable=False)
    num_questions = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    questions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now())
    __table_args__ = (
        CheckConstraint('num_questions > 0', name='positive_num_questions'),  # Added CheckConstraint
    )

class DebugExercise(Base):
    __tablename__ = 'debug_exercises'
    id = Column(Integer, primary_key=True)
    tech_stack_id = Column(Integer, ForeignKey('tech_stack.id', ondelete='CASCADE'), nullable=False)
    topic_ids = Column(ARRAY(Integer), nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    path_id = Column(UUID(as_uuid=False), unique=True)
    __table_args__ = (
        CheckConstraint('duration > 0', name='positive_duration'),  # Added CheckConstraint
    )
 
class HandsOn(Base):
    __tablename__ = 'hands_on'  # Fixed typo from _tablename__ to __tablename__
    id = Column(Integer, primary_key=True)
    tech_stack_id = Column(Integer, ForeignKey('tech_stack.id', ondelete='CASCADE'), nullable=False)
    topic_ids = Column(ARRAY(Integer), nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    path_id = Column(UUID(as_uuid=False), unique=True)
    __table_args__ = (
        CheckConstraint('duration > 0', name='positive_duration'),  # Added CheckConstraint
    )
 
class Test(Base):
    __tablename__ = 'tests'
    id = Column(Integer, primary_key=True)
    test_name = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    duration = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    created_by = Column(Integer, ForeignKey('employees.user_id'), nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id', ondelete='SET NULL'))
    debug_test_id = Column(Integer, ForeignKey('debug_exercises.id', ondelete='SET NULL'))
    handson_id = Column(Integer, ForeignKey('hands_on.id', ondelete='SET NULL'))
    __table_args__ = (
        CheckConstraint('quiz_id IS NOT NULL OR debug_test_id IS NOT NULL OR handson_id IS NOT NULL', name='test_has_component'),  # Added CheckConstraint
    )

class Collaborator(Base):
    __tablename__ = 'collaborators'
    id = Column(Integer, primary_key=True)
    cl_id = Column(Integer, ForeignKey('employees.user_id'))
    collaborator_id = Column(Integer, ForeignKey('employees.user_id'), nullable=False)
    topics = Column(Boolean, default=False)
    test_create = Column(Boolean, default=False)
    test_assign = Column(Boolean, default=False)
 
    owner = relationship('Employee', foreign_keys=[cl_id], back_populates='collaborations')
    collaborator = relationship('Employee', foreign_keys=[collaborator_id], back_populates='collaborated_with')


class TestAssign(Base):
    __tablename__ = 'test_assign'
    assign_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    test_id = Column(Integer, ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    status = Column(Enum(StatusType), nullable=False)
    assigned_date = Column(DateTime, default=func.now())
    completed_date = Column(DateTime)
    due_date = Column(DateTime)
    mail_sent = Column(Enum(MailStatus), nullable=False)
    assigned_by = Column(Integer, ForeignKey('employees.user_id'))
    debug_github_url = Column(String(200), nullable=True)
    handson_github_url = Column(String(200), nullable=True)
    __table_args__ = (
        UniqueConstraint('user_id', 'test_id', name='uniq_user_test_assign'),  # Added UniqueConstraint
    )
    test = relationship('Test', backref='assignments')

class QuizResult(Base):
    __tablename__ = 'quiz_results'
    result_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False)
    score = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, default=func.now())
    answers = Column(JSON, nullable=False)
    feedback_data = Column(JSON, nullable=True)
    __table_args__ = (
        CheckConstraint('score >= 0 AND score <= 100', name='valid_score'),  # Added CheckConstraint
    )

class DebugResult(Base):
    __tablename__ = 'debug_results'
    result_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    debug_id = Column(Integer, ForeignKey('debug_exercises.id', ondelete='CASCADE'), nullable=False)
    score = Column(Integer, nullable=False)
    feedback_data = Column(JSON, nullable=True)
    __table_args__ = (
        CheckConstraint('score >= 0 AND score <= 100', name='valid_score'),  # Added CheckConstraint
    )

class HandsOnResult(Base):  # Added HandsOnResult table
    __tablename__ = 'hands_on_results'
    result_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    handson_id = Column(Integer, ForeignKey('hands_on.id', ondelete='CASCADE'), nullable=False)
    score = Column(Integer, nullable=False)
    feedback_data = Column(JSON, nullable=True)
    __table_args__ = (
        CheckConstraint('score >= 0 AND score <= 100', name='valid_score'),  # Added CheckConstraint
    )

class EmployeeSkill(Base):
    __tablename__ = 'employee_skills'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    tech_stack_id = Column(Integer, ForeignKey('tech_stack.id', ondelete='CASCADE'), nullable=False)
    current_level = Column(Enum(DifficultyLevel), default=DifficultyLevel.beginner)
    employee = relationship('Employee', back_populates='skills')
    tech_stack = relationship('TechStack', back_populates='employee_skills')
    __table_args__ = (
        UniqueConstraint('employee_id', 'tech_stack_id', name='uniq_employee_tech_stack'),
    )
 
class SkillUpgrade(Base):
    __tablename__ = 'skill_upgrades'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    tech_stack_id = Column(Integer, ForeignKey('tech_stack.id', ondelete='CASCADE'), nullable=False)
    target_level = Column(Enum(DifficultyLevel), nullable=False)
    status = Column(Enum(StatusType), nullable=False)
    assigned_test_id = Column(Integer, ForeignKey('tests.id', ondelete='SET NULL'))
    start_time = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    __table_args__ = (
        UniqueConstraint('employee_id', 'tech_stack_id', 'target_level', name='uniq_skill_upgrade'),
    )

class Suggestion(Base):  # Updated column names for clarity
    __tablename__ = 'suggestions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    collaborator_id = Column(Integer, ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    capability_leader_id = Column(Integer, ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    tech_stack_id = Column(Integer, ForeignKey('tech_stack.id', ondelete='CASCADE'), nullable=False)
    message = Column(String, nullable=False)
    raised_at = Column(DateTime, server_default=func.now(), nullable=False)
    collaborator = relationship('Employee', foreign_keys=[collaborator_id])
    capability_leader = relationship('Employee', foreign_keys=[capability_leader_id])
    tech_stack = relationship('TechStack')