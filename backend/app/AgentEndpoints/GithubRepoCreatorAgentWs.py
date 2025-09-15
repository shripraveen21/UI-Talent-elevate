import os
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from ..Agents.GithubRepoCreatorAgent import GitHubRepoCreator, create_repo_api

from pydantic import BaseModel

class RepoCreateRequest(BaseModel):
    name: str
    description: str = ""
    gitignore_template: str = ""
    license_template: str = ""

logger = logging.getLogger(__name__)
router = APIRouter()

# @router.websocket("/ws/github-repo-creation")
# async def github_repo_creation_ws(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         # Step 1: Receive repo creation parameters from frontend
#         data = await websocket.receive_json()
#         repo_name = data.get("name")
#         description = data.get("description", "")
#         auto_init = data.get("auto_init", True)
#         gitignore_template = data.get("gitignore_template", "")
#         license_template = data.get("license_template", "")

#         if not repo_name:
#             await websocket.send_json({"type": "error", "content": "Missing required repository name"})
#             await websocket.close()
#             return

#         # Step 2: Read GitHub token from environment
#         github_token = os.getenv("GITHUB_TOKEN")
#         if not github_token:
#             await websocket.send_json({"type": "error", "content": "GitHub token not set in environment"})
#             await websocket.close()
#             return

#         # Step 3: Setup GitHubRepoCreator and agents
#         github_creator = GitHubRepoCreator(github_token)
#         user_proxy, github_assistant = setup_autogen_agents(github_creator)

#         # Step 4: Run repo creation workflow (with human approval)
#         # This is a blocking call, so run in executor to avoid blocking event loop
#         loop = asyncio.get_event_loop()
#         def run_creation():
#             from autogen_agentchat.teams import RoundRobinGroupChat
#             from autogen_agentchat.conditions import TextMentionTermination
#             termination = TextMentionTermination("TERMINATE")
#             team = RoundRobinGroupChat([user_proxy, github_assistant], termination_condition=termination)
#             task_message = f"""
#                 Please create a new GitHub repository with the following specifications:
#                 - Name: "{repo_name}"
#                 - Description: "{description}"
#                 - Initialize with README: {auto_init}
#                 - Gitignore template: {gitignore_template}
#                 - License template: {license_template}
#                 """
#             import asyncio
#             return asyncio.run(team.run(task=task_message))
#         await loop.run_in_executor(None, run_creation)

#         # Step 5: Send final result to frontend
#         await websocket.send_json({"type": "final", "content": "Repository creation process completed. Check your GitHub account for details."})
#         await websocket.close()

#     except WebSocketDisconnect:
#         logger.info("Client disconnected during GitHub repo creation")
#     except Exception as e:
#         logger.error(f"Error in /ws/github-repo-creation: {str(e)}")
#         try:
#             await websocket.send_json({"type": "error", "content": str(e)})
#         except Exception:
#             pass
#         await websocket.close()

from fastapi import Request
from fastapi.responses import JSONResponse

@router.post("/github-repo/create")
async def create_github_repo_endpoint(request: RepoCreateRequest):
    try:
        result = create_repo_api(
            repo_name=request.name,
            description=request.description,
            gitignore=request.gitignore_template,
            license_template=request.license_template
        )
        
        if result["success"]:
            return {
                "status": "success",
                "repository_url": result["repository_url"],
                "message": result["message"]
            }
        else:
            return {
                "status": "error",
                "error": result["error"],
                "message": result["message"]
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Internal server error"
        }
