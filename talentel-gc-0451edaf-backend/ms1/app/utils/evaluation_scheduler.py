import os

from ..models.models import DebugExercise, DebugResult, TestAssign, HandsOn, HandsOnResult
from .GithubRepoFetcher import GitHubRepoFetcher
import asyncio
from ..services.evaluator_service import evaluate_debug
from datetime import timedelta, datetime
from ..config.database import get_db


async def debug_evaluator(github_token=os.getenv("GITHUB_TOKEN"), repo_owner="Deloitte-US"):
    db = None
    try:
        db = next(get_db())

        # Get all evaluated assignments: (debug_id, user_id)
        evaluated_assignments = set(
            db.query(DebugResult.debug_id, DebugResult.user_id).all()
        )
        print("Evaluated assignments: ", evaluated_assignments)

        # Get all assignments that need evaluation
        debug_tests = db.query(DebugExercise).all()
        fetcher = GitHubRepoFetcher(github_token, owner=repo_owner)

        for debug_test in debug_tests:
            assigned_tests = db.query(TestAssign).filter(TestAssign.test_id == debug_test.id).all()
            print("Assign tests: ", assigned_tests)
            for assign in assigned_tests:
                assignment_key = (debug_test.id, assign.user_id)
                if assignment_key in evaluated_assignments:
                    print(f"[INFO] Assignment {assign.assign_id} for user {assign.user_id} already evaluated. Skipping.")
                    continue

                if assign.debug_github_url:
                    print("GitHub URL: ", assign.debug_github_url)
                    try:
                        if assign.assigned_date is None or debug_test.duration is None:
                            print(f"[WARN] Missing assigned_date or duration for assignment {assign.assign_id}")
                            continue
                        timestamp_dt = assign.assigned_date + timedelta(minutes=debug_test.duration)
                        timestamp = timestamp_dt.isoformat() + "Z"

                        repo_url = assign.debug_github_url
                        try:
                            repo_path = repo_url.split("github.com/")[1].replace(".git", "")
                            repo_full_name = repo_path
                        except Exception as parse_err:
                            print(f"[ERROR] Could not parse repo_full_name from {repo_url}: {parse_err}")
                            continue

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
                            asyncio.create_task(
                                evaluate_debug(fetch_result["local_path"], debug_test.path_id, user_id=assign.user_id)
                            )
                            print(f"[INFO] Evaluated and stored result for assignment {assign.assign_id}")
                        else:
                            print(f"[ERROR] GitHub fetch failed: {fetch_result.get('error')}")
                    except Exception as eval_err:
                        print(f"[ERROR] Evaluation failed for assignment {assign.assign_id}: {eval_err}")
    except Exception as e:
        print("Unable to perform scheduled debug evaluator:", e)
    finally:
        if db is not None:
            db.close()