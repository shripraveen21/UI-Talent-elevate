import os
import asyncio
from datetime import timedelta, datetime

from ..models.models import DebugExercise, DebugResult, TestAssign, HandsOn, HandsOnResult, Test
from .GithubRepoFetcher import GitHubRepoFetcher
from ..services.evaluator_service import evaluate_debug, evaluate_handson
from ..config.database import get_db

def get_unevaluated_debug_assignments(db):
    # Only get assignments where due date has passed
    debug_assignments = (
        db.query(TestAssign, Test, DebugExercise)
        .join(Test, TestAssign.test_id == Test.id)
        .join(DebugExercise, Test.debug_test_id == DebugExercise.id)
        .filter(
            Test.debug_test_id.isnot(None),
            TestAssign.due_date.isnot(None),
            TestAssign.due_date < datetime.utcnow()
        )
        .all()
    )
    evaluated = set(db.query(DebugResult.debug_id, DebugResult.user_id).all())
    unevaluated = [
        (assign, test, debug_test)
        for assign, test, debug_test in debug_assignments
        if (debug_test.id, assign.user_id) not in evaluated
    ]
    return unevaluated

def get_unevaluated_handson_assignments(db):
    handson_assignments = (
        db.query(TestAssign, Test, HandsOn)
        .join(Test, TestAssign.test_id == Test.id)
        .join(HandsOn, Test.handson_id == HandsOn.id)
        .filter(
            Test.handson_id.isnot(None),
            TestAssign.due_date.isnot(None),
            TestAssign.due_date < datetime.utcnow()
        )
        .all()
    )
    evaluated = set(db.query(HandsOnResult.handson_id, HandsOnResult.user_id).all())
    unevaluated = [
        (assign, test, handson_test)
        for assign, test, handson_test in handson_assignments
        if (handson_test.id, assign.user_id) not in evaluated
    ]
    return unevaluated

async def evaluate_unevaluated_debug_assignments(github_token=os.getenv("GITHUB_TOKEN"), repo_owner="Deloitte-US"):
    db = None
    try:
        db = next(get_db())
        print("Started debug evaluation ..........")
        fetcher = GitHubRepoFetcher(github_token, owner=repo_owner)
        unevaluated = get_unevaluated_debug_assignments(db)
        for assign, test, debug_test in unevaluated:
            if assign.debug_github_url and assign.assigned_date and debug_test.duration:
                timestamp_dt = assign.assigned_date + timedelta(minutes=debug_test.duration)
                timestamp = timestamp_dt.isoformat() + "Z"
                repo_url = assign.debug_github_url
                repo_path = repo_url.split("github.com/")[1].replace(".git", "")
                repo_full_name = repo_path
                branch = "main"
                target_dir = f"/tmp/{repo_full_name.replace('/', '_')}_{assign.assign_id}"
                fetch_result = fetcher.fetch_repo_at_commit(
                    repo_url=repo_url,
                    repo_full_name=repo_full_name,
                    branch=branch,
                    timestamp=timestamp,
                    assign_id=assign.assign_id,
                )
                if fetch_result.get("success"):
                    await evaluate_debug(fetch_result["local_path"], debug_test.path_id, user_id=assign.user_id)
                else:
                    print(f"[ERROR] GitHub fetch failed: {fetch_result.get('error')}")
    except Exception as e:
        print("Unable to perform scheduled debug evaluator:", e)
    finally:
        if db is not None:
            db.close()

async def evaluate_unevaluated_handson_assignments(github_token=os.getenv("GITHUB_TOKEN"), repo_owner="Deloitte-US"):
    db = None
    try:
        db = next(get_db())
        print("Evaluating handson assignments ..........")
        fetcher = GitHubRepoFetcher(github_token, owner=repo_owner)
        unevaluated = get_unevaluated_handson_assignments(db)
        for assign, test, handson_test in unevaluated:
            if assign.handson_github_url and assign.assigned_date and handson_test.duration:
                timestamp_dt = assign.assigned_date + timedelta(minutes=handson_test.duration)
                timestamp = timestamp_dt.isoformat() + "Z"
                repo_url = assign.handson_github_url
                repo_path = repo_url.split("github.com/")[1].replace(".git", "")
                repo_full_name = repo_path
                branch = "main"
                target_dir = f"/tmp/{repo_full_name.replace('/', '_')}_{assign.assign_id}"
                fetch_result = fetcher.fetch_repo_at_commit(
                    repo_url=repo_url,
                    repo_full_name=repo_full_name,
                    branch=branch,
                    timestamp=timestamp,
                    assign_id=assign.assign_id,
                )
                if fetch_result.get("success"):
                    await evaluate_handson(fetch_result["local_path"], handson_test.path_id, user_id=assign.user_id)
                else:
                    print(f"[ERROR] GitHub fetch failed: {fetch_result.get('error')}")
    except Exception as e:
        print("Unable to perform scheduled hands-on evaluator:", e)
    finally:
        if db is not None:
            db.close()
