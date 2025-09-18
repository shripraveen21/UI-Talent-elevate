import shutil
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from ..Agents.DebugGen.DebugEvaluatorWorkflow import agentic_debug_evaluation_workflow
from ..Agents.HandsONEvaluator import agentic_assignment_evaluation_workflow
from .debug_gen_service import save_debug_results, save_handson_results
import os
import stat
import time

def on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"[ERROR] Could not forcibly remove {path}: {e}")

def safe_cleanup(target_dir):
    if os.path.exists(target_dir):
        print(f"[DEBUG] Attempting to clean up: {target_dir}")
        try:
            shutil.rmtree(target_dir, onerror=on_rm_error)
            print(f"[INFO] Successfully cleaned up: {target_dir}")
        except Exception as cleanup_err:
            print(f"[WARN] Could not clean up target dir: {cleanup_err}")
            print(f"[DEBUG] Directory contents after failed cleanup: {os.listdir(target_dir)}")
            time.sleep(1)
            # Optionally, try again
            try:
                shutil.rmtree(target_dir, onerror=on_rm_error)
            except Exception as e:
                print(f"[ERROR] Second cleanup attempt failed: {e}")

async def evaluate_debug(user_path, unique_id, user_id):
    try:
        gen_proj_dir = os.getenv("GEN_PROJ_DIR", "GeneratedProject")
        buggy_proj_dir = os.getenv("BUGGY_PROJ_DIR", "BugInjectedProject")
        manifest = os.path.join(buggy_proj_dir, unique_id, 'project', 'bug_manifest.json')
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        results = await agentic_debug_evaluation_workflow(
            bugged_dir=os.path.join(buggy_proj_dir, unique_id, 'project'),
            bug_manifest_path=manifest,
            original_dir=os.path.join(gen_proj_dir, unique_id, 'project'),
            model_client=model_client,
            user_dir=user_path
        )
        await save_debug_results(path_id=unique_id, user_id=user_id, results=results)

    except Exception as e:
        print(e)
    finally:
        try:
            safe_cleanup(user_path)
            print(f"[INFO] Cleaned up directory: {user_path}")
        except Exception as cleanup_err:
            print(f"[ERROR] Failed to clean up (es) {user_path}: {cleanup_err}")


async def evaluate_handson(user_path, unique_id, user_id):
    try:
        handson_proj_dir = os.getenv("HANDSON_PROJ_DIR", "HandsonProject")

        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )

        results = await agentic_assignment_evaluation_workflow(
            srs_path=os.path.join(handson_proj_dir, unique_id, 'project'),
            readme_path=os.path.join(handson_proj_dir, unique_id, 'project'),
            model_client=model_client,
            codebase_dir=user_path
        )

        await save_handson_results(path_id=unique_id, user_id=user_id, results=results)

    except Exception as e:
        print(e)
    finally:
        try:
            safe_cleanup(user_path)
            print(f"[INFO] Cleaned up directory: {user_path}")
        except Exception as cleanup_err:
            print(f"[ERROR] Failed to clean up (es) {user_path}: {cleanup_err}")
