from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from .controllers.skill_upgrade_controller import router as skill_upgrade_router
from .AgentEndpoints.DebugExerciseAgentWs import router as debug_exercise_router
from .AgentEndpoints.EpicAgentWs import router as agent_chat_router
from .AgentEndpoints.McqAgentWs import router as mcq_agent_router
from .AgentEndpoints.TopicAgentWS import router as topic_agent_router
from .AgentEndpoints.GithubRepoCreatorAgentWs import router as github_router
from .config.database import SessionLocal, engine
from .controllers.auth_controller import router as auth_router
from .controllers.employee_controller import router as employee_router
from .controllers.rbac_controller import router as rbac_router
from .controllers.tech_stack_controller import router as tech_stack_router
from .controllers.test_assign_controller import router as test_assign_router
from .controllers.test_controller import router as test_router
from .controllers.topics_controller import router as topic_router
from .controllers.collaborators_controller import router as collaborators_router
from .models.models import *

bearer_scheme = HTTPBearer()

Base.metadata.create_all(bind=engine)
app = FastAPI()



# CORS configuration to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200",'*'],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.include_router(auth_router)
app.include_router(rbac_router)

from .controllers.debug_test_controller import router as debug_test_router
app.include_router(debug_test_router)

from .controllers.employee_dashboard_controller import router as employee_dashboard_router
app.include_router(employee_dashboard_router)
app.include_router(tech_stack_router)
app.include_router(topic_router)
app.include_router(collaborators_router)
app.include_router(test_router)
app.include_router(agent_chat_router)
app.include_router(mcq_agent_router)
app.include_router(debug_exercise_router)
app.include_router(topic_agent_router)
app.include_router(employee_router)
app.include_router(test_assign_router)
app.include_router(skill_upgrade_router)

from .controllers.feedback_pdf_controller import router as feedback_pdf_router
app.include_router(feedback_pdf_router)
app.include_router(github_router)
