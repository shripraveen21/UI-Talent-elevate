from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .config.database import SessionLocal, engine, Base
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from .models.models import *
from .AgentEndpoints.EpicAgentWs import router as agent_chat_router
from .AgentEndpoints.McqAgentWs import router as mcq_agent_router
from .AgentEndpoints.DebugExerciseAgentWs import router as debug_exercise_router
from .controllers.auth_controller import router as auth_router
from .controllers.rbac_controller import router as rbac_router
from .controllers.topics_controller import router as topic_router
from .controllers.test_controller import router as test_router
from .AgentEndpoints.TopicAgentWS import router as topic_agent_router
from .controllers.tech_stack_controller import router as tech_stack_router
from .controllers.employee_controller import router as employee_router
from .controllers.test_assign_controller import router as test_assign_router

bearer_scheme = HTTPBearer()

Base.metadata.create_all(bind=engine)
app = FastAPI()



# CORS configuration to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "*"],  # Allow Angular dev server and all origins (including ngrok)
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


from .controllers.employee_dashboard_controller import router as employee_dashboard_router
app.include_router(employee_dashboard_router)
app.include_router(tech_stack_router)
app.include_router(topic_router)
app.include_router(test_router)
app.include_router(agent_chat_router)
app.include_router(mcq_agent_router)
app.include_router(debug_exercise_router)
app.include_router(topic_agent_router)
app.include_router(employee_router)
app.include_router(test_assign_router)
