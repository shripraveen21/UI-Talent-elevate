from sqlalchemy import or_
from ..models.models import DebugExercise, Employee, HandsOn, Test, TestAssign, StatusType
from ..schemas.test_schema import AssignTestRequest, TestFilter,TestOut
from sqlalchemy.orm import Session
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

def list_tests(db: Session, filters: TestFilter):
    query = db.query(Test)
    if filters.get("search"):
        search = f"%{filters.get('search')}%"
        query = query.filter(Test.test_name.ilike(search))
    total = query.count()
    tests = query.offset((filters.get("page")-1)*filters.get("page_size")).limit(filters.get("page_size")).all()
    return total, tests

from ..utils.email import send_assignment_email

import requests
import base64
import os
import time
from typing import Dict, Any

def push_files_to_github(repo_full_name: str, files_dir: str, github_token: str, 
                        commit_message: str = "Initial bugged code commit") -> Dict[str, Any]:
    """
    Push all files from files_dir to the root of the repo using GitHub API.
    Returns a dictionary with success status and details.
    """
    if not os.path.exists(files_dir):
        return {"success": False, "error": f"Directory {files_dir} does not exist"}
    
    if not github_token:
        return {"success": False, "error": "GitHub token is empty"}
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-Script"  # GitHub requires a User-Agent
    }
    
    # Test authentication first
    auth_test = requests.get("https://api.github.com/user", headers=headers)
    if auth_test.status_code != 200:
        return {"success": False, "error": f"Authentication failed: {auth_test.status_code} - {auth_test.text}"}
    
    print(f"[DEBUG] Authenticated as: {auth_test.json().get('login', 'Unknown')}")
    
    # Check if repo exists
    repo_check = requests.get(f"https://api.github.com/repos/{repo_full_name}", headers=headers)
    if repo_check.status_code != 200:
        return {"success": False, "error": f"Repository {repo_full_name} not accessible: {repo_check.status_code}"}
    
    print(f"[DEBUG] Repository {repo_full_name} is accessible")
    
    uploaded_files = []
    failed_files = []
    
    # Walk through all files in the directory
    for root, dirs, files in os.walk(files_dir):
        print(f"[DEBUG] Processing directory: {root}")
        print(f"[DEBUG] Found {len(files)} files in this directory")
        
        for file in files:
            # Skip unwanted files
            if file.endswith('.orig') or file in ['bug_hints.json', 'bug_manifest.json', 'manifest.json']:
                print(f"[DEBUG] Skipping file: {file}")
                continue
            
            file_path = os.path.join(root, file)
            print(f"[DEBUG] Processing file: {file_path}")
            
            # Check if file is readable
            if not os.path.isfile(file_path):
                print(f"[WARNING] {file_path} is not a regular file, skipping")
                continue
            
            try:
                with open(file_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode()
                print(f"[DEBUG] Successfully read file: {file_path} ({len(content)} chars base64)")
            except Exception as e:
                error_msg = f"Failed to read file {file_path}: {str(e)}"
                print(f"[ERROR] {error_msg}")
                failed_files.append({"file": file_path, "error": error_msg})
                continue
            
            # Build the path in the repo (relative to files_dir)
            rel_path = os.path.relpath(file_path, files_dir)
            # Convert Windows paths to Unix paths for GitHub
            repo_path = rel_path.replace(os.sep, '/')
            print(f"[DEBUG] Repo path will be: {repo_path}")
            
            # GitHub API URL
            url = f"https://api.github.com/repos/{repo_full_name}/contents/{repo_path}"
            print(f"[DEBUG] GitHub API URL: {url}")
            
            # Check if file exists to get its sha
            sha = None
            try:
                get_resp = requests.get(url, headers=headers)
                if get_resp.status_code == 200:
                    file_info = get_resp.json()
                    if isinstance(file_info, dict) and "sha" in file_info:
                        sha = file_info["sha"]
                        print(f"[DEBUG] File exists, got SHA: {sha[:8]}...")
                    else:
                        print(f"[DEBUG] Unexpected response format: {type(file_info)}")
                elif get_resp.status_code == 404:
                    print(f"[DEBUG] File doesn't exist yet, will create new")
                else:
                    print(f"[WARNING] Unexpected status when checking file existence: {get_resp.status_code}")
            except Exception as e:
                print(f"[WARNING] Error checking if file exists: {str(e)}")
            
            # Prepare the data for upload
            data = {
                "message": commit_message,
                "content": content
            }
            if sha:
                data["sha"] = sha
            
            # Upload the file
            try:
                response = requests.put(url, headers=headers, json=data)
                print(f"[DEBUG] Upload response status: {response.status_code}")
                
                if response.status_code in [201, 200]:
                    print(f"[SUCCESS] Uploaded {repo_path}")
                    uploaded_files.append(repo_path)
                else:
                    error_msg = f"Failed to upload {repo_path}: {response.status_code} - {response.text}"
                    print(f"[ERROR] {error_msg}")
                    failed_files.append({"file": repo_path, "error": error_msg})
                
                # Rate limiting protection
                time.sleep(0.1)  # Small delay between requests
                
            except Exception as e:
                error_msg = f"Exception during upload of {repo_path}: {str(e)}"
                print(f"[ERROR] {error_msg}")
                failed_files.append({"file": repo_path, "error": error_msg})
    
    return {
        "success": len(failed_files) == 0,
        "uploaded_files": uploaded_files,
        "failed_files": failed_files,
        "total_uploaded": len(uploaded_files),
        "total_failed": len(failed_files)
    }


def assign_test(db: Session, request: AssignTestRequest, assigned_by: int):
    """
    Assigns a test to users, creates GitHub repos for debug/hands-on assignments,
    pushes files, adds collaborators, stores repo URLs, and sends notification email.
    """
    assignments = []
    from ..Agents.GithubRepoCreatorAgent import create_repo_api, GitHubRepoCreator

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("GITHUB_TOKEN not set in environment.")
        return assignments

    # Fetch the test object to check debug_test_id and handson_id
    test_obj = db.query(Test).filter(Test.id == request.test_id).first()
    debug_test_id = getattr(test_obj, "debug_test_id", None)
    handson_id = getattr(test_obj, "handson_id", None)

    for user_id in request.user_ids:
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        user_name = getattr(employee, "name", None)
        github_username = employee.email.split('.')[0].replace('@', '_')
        if not user_name:
            print(f"No name found for user {user_id}, skipping repo creation.")
            continue

        debug_github_url = None
        handson_github_url = None

        # Handle debug assignment
        if debug_test_id:
            debug_ex = db.query(DebugExercise).filter(DebugExercise.id == debug_test_id).first()
            debug_path_id = getattr(debug_ex, "path_id", None)
            bugged_code_dir = os.path.join(
                os.getcwd(),
                "BugInjectedProject",
                debug_path_id,
                "project"
            )
            if os.path.exists(bugged_code_dir):
                repo_name = f"debug-{debug_path_id}-{user_id}"
                repo_desc = f"Debug exercise for test {request.test_id} assigned to {user_name}"
                repo_result = create_repo_api(repo_name, description=repo_desc)
                if repo_result.get("success"):
                    debug_github_url = repo_result.get("repository_url")
                    github_creator = GitHubRepoCreator(github_token)
                    collab_result = github_creator.add_collaborator(repo_name, github_username)
                    if collab_result["success"]:
                        print(f"[SUCCESS] Added collaborator '{github_username}' to repo '{repo_name}'")
                    else:
                        print(f"[ERROR] Failed to add collaborator '{github_username}': {collab_result['message']}")
                    repo_full_name = f"Deloitte-US/{repo_name}"
                    push_result = push_files_to_github(repo_full_name, bugged_code_dir, github_token)
                    if push_result["success"]:
                        print(f"[SUCCESS] Uploaded files for debug assignment to {repo_full_name}")
                    else:
                        print(f"[ERROR] Failed to upload files for debug assignment: {push_result['failed_files']}")
                else:
                    print(f"[ERROR] Debug repo creation failed: {repo_result.get('error')}")
            else:
                print(f"[ERROR] BugInjectedProject directory not found for path_id {debug_path_id}")

        # Handle hands-on assignment
        if handson_id:
            handson_ex = db.query(HandsOn).filter(HandsOn.id == handson_id).first()
            handson_path_id = getattr(handson_ex, "path_id", None)
            handson_code_dir = os.path.join(
                os.getcwd(),
                "GeneratedHandsON",
                handson_path_id,
                "project"
            )
            if os.path.exists(handson_code_dir):
                repo_name = f"handson-{handson_path_id}-{user_id}"
                repo_desc = f"Hands-on exercise for test {request.test_id} assigned to {user_name}"
                repo_result = create_repo_api(repo_name, description=repo_desc)
                if repo_result.get("success"):
                    handson_github_url = repo_result.get("repository_url")
                    github_creator = GitHubRepoCreator(github_token)
                    collab_result = github_creator.add_collaborator(repo_name, github_username)
                    if collab_result["success"]:
                        print(f"[SUCCESS] Added collaborator '{github_username}' to repo '{repo_name}'")
                    else:
                        print(f"[ERROR] Failed to add collaborator '{github_username}': {collab_result['message']}")
                    repo_full_name = f"Deloitte-US/{repo_name}"
                    push_result = push_files_to_github(repo_full_name, handson_code_dir, github_token)
                    if push_result["success"]:
                        print(f"[SUCCESS] Uploaded files for hands-on assignment to {repo_full_name}")
                    else:
                        print(f"[ERROR] Failed to upload files for hands-on assignment: {push_result['failed_files']}")
                else:
                    print(f"[ERROR] Hands-on repo creation failed: {repo_result.get('error')}")
            else:
                print(f"[ERROR] GeneratedHandsON directory not found for path_id {handson_path_id}")

        # Only after all repo/collaborator/file operations, create the assignment record
        assignment = TestAssign(
            user_id=user_id,
            test_id=request.test_id,
            status = StatusType.assigned,
            due_date=request.due_date,
            mail_sent="Not_sent",
            assigned_by=assigned_by,
            debug_github_url=debug_github_url,
            handson_github_url=handson_github_url
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Only send mail after assignment is saved
        email_sent = send_assignment_email(
            db,
            user_id,
            request.test_id,
            request.due_date,
            debug_github_url=debug_github_url,
            handson_github_url=handson_github_url
        )
        assignment.mail_sent = "Sent" if email_sent else "Failed"
        db.commit()
        db.refresh(assignment)
        assignments.append(assignment)

    return assignments
