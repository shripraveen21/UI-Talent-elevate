import asyncio
import os
from datetime import datetime
from ..services.evaluator_service import evaluate_debug, evaluate_handson
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from ..utils.GithubRepoFetcher import GitHubRepoFetcher
from ..services.rbac_service import RBACService
from ..config.database import get_db
from ..models.models import DebugExercise, DebugResult, HandsOnResult, HandsOn, Employee, TestAssign, Test

router = APIRouter()

@router.get("/debug/{debug_id}")
def get_user_feedback(
        debug_id: int, user_id: int,
        db: Session = Depends(get_db)
):
    try:
        debug = db.query(DebugResult).filter(
            DebugResult.debug_id == debug_id,
            DebugResult.user_id == user_id
        ).first()
        return debug.feedback_data

    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(500, detail="Something went wrong")


@router.get("/handson/{handson_id}")
def get_user_feedback_handson(
        handson_id: int, user_id: int,
        db: Session = Depends(get_db)
):
    try:
        handson = db.query(HandsOnResult).filter(
            HandsOnResult.handson_id == handson_id,
            HandsOnResult.user_id == user_id
        ).first()
        return handson.feedback_data
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(500, detail="Something went wrong")

@router.post("/evaluate/debug/{test_id}")
async def evaluate_feedback(
        test_id: int, user_payload = Depends(RBACService.get_current_user),
        db: Session = Depends(get_db)
):
    try:
        print("start debug")
        user = db.query(Employee).filter(Employee.email == user_payload.get('sub')).first()
        if not user:
            raise HTTPException(404, detail="User not found")

        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            raise HTTPException(404, detail="Test not found")
        
        debug_id = test.debug_test_id

        debug_test = db.query(DebugExercise).filter(
            DebugExercise.id == debug_id
        ).first()
        if not debug_test:
            raise HTTPException(404, detail="Debug exercise not found")
        debug_res = db.query(DebugResult).filter(
            DebugResult.debug_id == debug_id,
            DebugResult.user_id == user.user_id
        ).first()
        if debug_res:
            raise HTTPException(404, detail="Debug Result already exists")
        test = db.query(Test.id).filter(
            Test.debug_test_id == debug_id,
        ).first()
        if not test:
            raise HTTPException(404, detail="Test not found")
        assigned = db.query(TestAssign).filter(
            TestAssign.user_id == user.user_id,
            TestAssign.test_id == test.id
        ).first()
        if not assigned:
            raise HTTPException(404, detail="Assignment not found")
        if not assigned.debug_github_url:
            raise HTTPException(404, detail="Assignment not found")
        fetcher = GitHubRepoFetcher(os.getenv("GITHUB_TOKEN"))
        repo_url = assigned.debug_github_url
        repo_path = repo_url.split("github.com/")[1].replace(".git", "")
        repo_full_name = repo_path
        branch = "main"
        target_dir = f"/tmp/{repo_full_name.replace('/', '_')}_{assigned.assign_id}"
        fetch_result = fetcher.fetch_repo_at_commit(
            repo_url=repo_url,
            repo_full_name=repo_full_name,
            branch=branch,
            timestamp=datetime.utcnow().isoformat() + "Z",
            assign_id=assigned.assign_id,
        )
        if fetch_result.get("success"):
            asyncio.create_task(evaluate_debug(fetch_result["local_path"], debug_test.path_id, user_id=assigned.user_id))
            return {"status": "Evaluation started"}
        else:
            print(f"[ERROR] GitHub fetch failed: {fetch_result.get('error')}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(500, detail="Something went wrong")

@router.post("/evaluate/handson/{test_id}")
async def evaluate_handson_feedback(
        test_id: int,
        user_payload=Depends(RBACService.get_current_user),
        db: Session = Depends(get_db)
):
    print("receieved")
    try:
        user = db.query(Employee).filter(Employee.email == user_payload.get('sub')).first()
        if not user:
            raise HTTPException(404, detail="User not found")

        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            raise HTTPException(404, detail="Test not found")

        
        print("asfa")
        handson_id = test.handson_id
        print(handson_id,"fa")

        handson_test = db.query(HandsOn).filter(
            HandsOn.id == handson_id
        ).first()
        if not handson_test:
            raise HTTPException(404, detail="HandsOn exercise not found")

        handson_res = db.query(HandsOnResult).filter(
            HandsOnResult.handson_id == handson_id,
            HandsOnResult.user_id == user.user_id
        ).first()
        if handson_res:
            raise HTTPException(404, detail="HandsOn Result already exists")

        test = db.query(Test.id).filter(
            Test.handson_id == handson_id,
        ).first()
        if not test:
            raise HTTPException(404, detail="Test not found")

        assigned = db.query(TestAssign).filter(
            TestAssign.user_id == user.user_id,
            TestAssign.test_id == test.id
        ).first()
        if not assigned or not assigned.handson_github_url:
            raise HTTPException(404, detail="Assignment not found")

        fetcher = GitHubRepoFetcher(os.getenv("GITHUB_TOKEN"))
        repo_url = assigned.handson_github_url
        repo_path = repo_url.split("github.com/")[1].replace(".git", "")
        repo_full_name = repo_path
        branch = "main"
        target_dir = f"/tmp/{repo_full_name.replace('/', '_')}_{assigned.assign_id}"

        fetch_result = fetcher.fetch_repo_at_commit(
            repo_url=repo_url,
            repo_full_name=repo_full_name,
            branch=branch,
            timestamp=datetime.utcnow().isoformat() + "Z",
            assign_id=assigned.assign_id,
        )

        if fetch_result.get("success"):
            asyncio.create_task(evaluate_handson(fetch_result["local_path"], handson_test.path_id, user_id=assigned.user_id))
            return {"status": "Evaluation started"}
        else:
            print(f"[ERROR] GitHub fetch failed: {fetch_result.get('error')}")
            raise HTTPException(500, detail="GitHub fetch failed")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(500, detail="Something went wrong")