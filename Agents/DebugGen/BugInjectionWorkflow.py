import os
import re
import json
import shutil
from pathlib import Path
import asyncio
import ast
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

load_dotenv()

# --- File System Tool ---
class FileSystemTool:
    @staticmethod
    def read_file(file_path):
        path = Path(file_path)
        if path.exists():
            with open(path, 'r') as f:
                return f.read()
        return None

    @staticmethod
    def write_file(file_path, content):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return True

    @staticmethod
    def list_dir(dir_path):
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            return [str(p) for p in path.iterdir()]
        return []

    @staticmethod
    def copy_tree(src, dst):
        if Path(dst).exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

# --- Utility: Get all files and functions ---
def get_all_files(project_dir):
    file_list = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), project_dir)
            file_list.append(rel_path.replace("\\", "/"))
    return file_list

def get_functions_in_file(file_path):
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    except Exception:
        return []

def get_file_function_map(project_dir, file_list):
    file_func_map = {}
    for file in file_list:
        if file.endswith(".py"):
            abs_path = os.path.join(project_dir, file)
            file_func_map[file] = get_functions_in_file(abs_path)
    return file_func_map

# --- Safe JSON parsing ---
def safe_parse_agent_response(response):
    # Remove tool logs and blank lines
    lines = response.splitlines()
    json_lines = []
    for line in lines:
        if line.strip().startswith("<|FileSystemTool|>"):
            continue
        if not line.strip():
            continue
        json_lines.append(line)
    response = "\n".join(json_lines).strip()
    # Remove markdown code fences
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()
    # Now try to parse the first valid JSON object
    matches = re.findall(r'(\{.*\})', response, re.DOTALL)
    if not matches:
        print("Raw agent response for debugging:\n", response)
        raise ValueError("No valid JSON found in response.")
    json_str = max(matches, key=len)
    try:
        return json.loads(json_str)
    except Exception as e:
        print("Failed to parse extracted JSON:", json_str)
        raise

def compare_structures(original, modified):
    # Returns True if structure is preserved, False otherwise
    for file, items in original.items():
        if file not in modified:
            print(f"File missing after injection: {file}")
            return False
        if isinstance(items, str) or isinstance(modified[file], str):
            print(f"Parse error in {file}")
            return False
        orig_set = set((t, n) for t, n, *_ in items)
        mod_set = set((t, n) for t, n, *_ in modified[file])
        if orig_set != mod_set:
            print(f"Structural mismatch in {file}: {orig_set} vs {mod_set}")
            return False
    return True

def extract_project_structure(project_dir):
    structure = {}
    for file_path in Path(project_dir).rglob("*.py"):
        rel_path = str(file_path.relative_to(project_dir))
        try:
            with open(file_path, "r") as f:
                tree = ast.parse(f.read())
            file_struct = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    file_struct.append(("function", node.name, ast.unparse(node.args)))
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    file_struct.append(("class", node.name, methods))
            structure[rel_path] = file_struct
        except Exception as e:
            structure[rel_path] = f"Parse error: {e}"
    return structure


def restore_skeletons(project_dir, original_structure):
    for file, items in original_structure.items():
        file_path = Path(project_dir) / file
        lines = []
        if not file_path.exists():
            print(f"Restoring missing file: {file}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            with open(file_path, "r") as f:
                lines = f.readlines()
        # Build a set of existing function/class names
        existing = set()
        try:
            tree = ast.parse("".join(lines)) if lines else ast.parse("")
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    existing.add(("function", node.name))
                elif isinstance(node, ast.ClassDef):
                    existing.add(("class", node.name))
        except Exception:
            pass  # If file is broken, we'll restore everything

        with open(file_path, "a") as f:
            for item in items:
                if isinstance(item, str):
                    continue  # skip parse errors
                kind, name, details = item
                if (kind, name) not in existing:
                    if kind == "function":
                        f.write(f"\ndef {name}{details}:\n    pass\n")
                    elif kind == "class":
                        f.write(f"\nclass {name}:\n    pass\n")


# --- Helper Functions for Topic-Aware Bug Selection ---
def map_location_to_topic(candidates):
    """Builds a (file, location) -> topic map from candidates."""
    return {(c['file'], c['location']): c['topic'] for c in candidates}

def add_topics_to_bugs(bug_plans, candidates):
    """Adds topic info to each bug in bug_plans using candidates."""
    loc2topic = map_location_to_topic(candidates)
    for bug in bug_plans:
        bug['topic'] = loc2topic.get((bug['file'], bug['location']))
    return bug_plans

def group_bugs_by_topic(bug_plans):
    """Returns a dict: topic -> list of bugs."""
    grouped = {}
    for bug in bug_plans:
        topic = bug.get('topic')
        if topic:
            grouped.setdefault(topic, []).append(bug)
    return grouped

# --- Agents ---
class BugDiscoveryAgent:
    def __init__(self, model_client, project_dir, existing_files, file_func_map):
        self.agent = AssistantAgent(
            name="bug_discovery",
            model_client=model_client,
            system_message=f"""
You are a senior software engineer specializing in code review and software quality.

You have access to a FileSystemTool that can read files, list directories, and inspect code in {project_dir}.

Your tasks:
1. Use the FileSystemTool to inspect ONLY the following files in the codebase: {json.dumps(existing_files)}
2. For each file, you may use these functions/classes: {json.dumps(file_func_map)}
3. Identify functions, classes, or code blocks where bugs related to these topics could be educationally injected.
4. For each candidate, specify file, location (function or class name), relevant topic, and rationale.
5. Output ONLY valid JSON in the following format (do NOT output a raw list):
{{
    "candidates": [
        {{
            "file": "src/utils.py",
            "location": "function filter_items",
            "topic": "Loops",
            "rationale": "Loop logic can be easily misunderstood."
        }},
        ...
    ]
}}
Before outputting, double-check that all referenced files and locations exist in the provided list.
End with TERMINATE.
"""
        )

    async def discover_bugs(self, project_dir, topics):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
You may use the FileSystemTool to read files and list directories as needed.
Analyze the codebase in {project_dir} and identify candidate locations for bug injection related to: {', '.join(topics)}.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "bug_discovery":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        obj = safe_parse_agent_response(json_content)
        if isinstance(obj, dict) and "candidates" in obj:
            return obj["candidates"]
        elif isinstance(obj, list):
            return obj
        else:
            raise ValueError("Agent response did not contain a 'candidates' list or key.")

class BugDesignAgent:
    def __init__(self, model_client, project_dir):
        self.agent = AssistantAgent(
            name="bug_designer",
            model_client=model_client,
            system_message=f"""
You are a senior developer and educator.

You have access to a FileSystemTool to inspect code in {project_dir}.

Your tasks:
1. For each candidate location (provided below), use the FileSystemTool to inspect the code and design a realistic bug aligned with the topic.
2. **When designing the buggy code, make only the minimal change required to introduce the bug.**
3. **Preserve all original formatting, comments, and unrelated code. Do not remove or alter any code outside the specific bug location.**
4. **Do not change the function or class signature, return type, or docstring unless the bug specifically requires it.**
5. Specify bug type, code change, educational value, and a hint for learners.
6. Only use the provided candidate locations. Do NOT invent new files or functions.
7. Output ONLY valid JSON in the following format (do NOT output a raw list):
{{
    "bugs": [
        {{
            "file": "src/utils.py",
            "location": "function filter_items",
            "type": "Misplaced Break",
            "description": "...",
            "original_code": "...",
            "buggy_code": "...",
            "hint": "..."
        }},
        ...
    ]
}}
Before outputting, verify that all files and locations match the provided candidates.
**When producing 'buggy_code', copy the original code and make only the minimal change needed for the bug, preserving all other lines and formatting.**
End with TERMINATE.
"""
        )

    async def design_bugs(self, project_dir, candidates, topics):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Candidates: {json.dumps(candidates)}
Topics: {', '.join(topics)}
You may use the FileSystemTool to inspect code as needed.
For each candidate location, design a realistic, educational bug related to the topic.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "bug_designer":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        obj = safe_parse_agent_response(json_content)
        if isinstance(obj, dict) and "bugs" in obj:
            return obj["bugs"]
        elif isinstance(obj, list):
            return obj
        else:
            raise ValueError("Agent response did not contain a 'bugs' list or key.")

class BugSelectionAgent:
    def __init__(self, model_client):
        self.agent = AssistantAgent(
            name="bug_selector",
            model_client=model_client,
            system_message="""
You are a senior educator. Given grouped bugs by topic, select the most educational and representative bugs for each topic.
You may select more than one per topic if they cover different concepts or error types.
Output ONLY valid JSON in this format:
{
    "selected_bugs": [
        { ... bug dict ... },
        ...
    ]
}
End with TERMINATE.
"""
        )

    async def select_bugs(self, grouped_bugs):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Here are bugs grouped by topic:
{json.dumps(grouped_bugs, indent=2)}
Select the most educational bugs per topic (may be more than one per topic).
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "bug_selector":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        obj = safe_parse_agent_response(json_content)
        return obj.get("selected_bugs", [])

class BugInjectionAgent:
    def __init__(self, model_client, project_dir, existing_files):
        self.agent = AssistantAgent(
            name="bug_injector",
            model_client=model_client,
            system_message=f"""
You are a senior software engineer and educator specializing in software quality.

You have access to a FileSystemTool that can read, write, and list files/directories in {project_dir}.

Your tasks:
1. Use the FileSystemTool to read and modify ONLY the following files: {json.dumps(existing_files)}
2. For each bug, provide:
   - The file and location (line or function)
   - The original code snippet
   - The modified (buggy) code snippet
   - A description of the bug and its educational value
   - The type/category of bug
   - A hint to help a learner fix the bug
3. **When injecting the bug, make only the minimal change required to introduce the bug. Do not alter or remove unrelated code, comments, or formatting.**
4. **Preserve the original structure, indentation, and docstrings.**
5. Inject the bugs by modifying the relevant files using the FileSystemTool. Do NOT inject more than one bug per function or code block.
6. Output ONLY valid JSON in the following format (do NOT output a raw list):
{{
    "bugs": [
        {{
            "file": "src/utils.py",
            "location": "function filter_items",
            "type": "Misplaced Break",
            "description": "...",
            "original_code": "...",
            "buggy_code": "...",
            "hint": "..."
        }},
        ...
    ]
}}
Double-check that all referenced files exist and that you do not invent new files or functions.
**When producing 'buggy_code', copy the original code and make only the minimal change needed for the bug, preserving all other lines and formatting.**
End with TERMINATE.
"""
        )

    async def inject_bugs(self, project_dir, topics):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
You may use the FileSystemTool to read and write files as needed.
Analyze the codebase in {project_dir} and inject realistic, educational bugs related to these topics: {', '.join(topics)}.
Document each bug as specified, including a hint to help a learner fix the bug.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "bug_injector":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        print("Agent response content:\n", json_content)
        if not json_content.strip():
            raise ValueError("Agent did not return any JSON content. Check agent prompt and project directory.")
        obj = safe_parse_agent_response(json_content)
        if isinstance(obj, dict) and "bugs" in obj:
            return obj["bugs"]
        elif isinstance(obj, list):
            return obj
        else:
            raise ValueError("Agent response did not contain a 'bugs' list or key.")

class CriticAgent:
    def __init__(self, model_client, project_dir, existing_files):
        self.agent = AssistantAgent(
            name="critic_agent",
            model_client=model_client,
            system_message=f"""
You are a senior code reviewer and educator.

Your tasks:
1. Review the bug manifest and injected code in {project_dir}.
2. For each bug, assess:
   - Is the bug realistic and educational?
   - Is the hint clear and actionable?
   - Did the agent invent any files or functions not present in the original codebase ({json.dumps(existing_files)})?
3. Suggest improvements for future bug injection.
4. Output ONLY valid JSON in the following format:
{{
    "feedback": [
        {{
            "bug_name": "...",
            "assessment": "...",
            "improvement_suggestion": "..."
        }},
        ...
    ],
    "overall_critique": "..."
}}
End with TERMINATE.
"""
        )

    async def provide_feedback(self, project_dir, bug_manifest, bug_hints):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Review the following bug manifest and hints:
Manifest: {json.dumps(bug_manifest)}
Hints: {json.dumps(bug_hints)}
Provide feedback as specified.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "critic_agent":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        obj = safe_parse_agent_response(json_content)
        return obj

# --- Manifest Writing ---
def apply_bugs_and_write_manifests(bugged_dir, bugs):
    bug_manifest = {}
    bug_hints = {}
    for idx, bug in enumerate(bugs):
        file_path = Path(bugged_dir) / bug["file"]
        if not file_path.exists():
            print(f"Warning: Skipping bug for non-existent file {bug['file']}")
            continue
        backup_path = file_path.with_suffix(file_path.suffix + ".orig")
        if not backup_path.exists():
            shutil.copy2(file_path, backup_path)
        with open(file_path, 'w') as f:
            f.write(bug["buggy_code"])
        bug_name = f"{bug['file']}::{bug['location']}::{bug['type']}::{idx}"
        bug_manifest[bug_name] = {
            "file": bug["file"],
            "location": bug["location"],
            "type": bug["type"],
            "description": bug["description"]
        }
        bug_hints[bug_name] = {
            "detail": bug["description"],
            "hint": bug["hint"]
        }
    with open(Path(bugged_dir) / "bug_manifest.json", 'w') as mf:
        json.dump(bug_manifest, mf, indent=2)
    with open(Path(bugged_dir) / "bug_hints.json", 'w') as hf:
        json.dump(bug_hints, hf, indent=2)

# --- Main Workflow ---
async def bug_injection_workflow(model_client, unique_id, topics):
    original_dir = f"GeneratedProject/{unique_id}/project"
    bugged_dir = f"BugInjectedProject/{unique_id}/project"
    FileSystemTool.copy_tree(original_dir, bugged_dir)

    # Gather file and function lists
    existing_files = get_all_files(bugged_dir)
    file_func_map = get_file_function_map(bugged_dir, existing_files)

    # 1. Discover bug opportunities
    discovery_agent = BugDiscoveryAgent(model_client, bugged_dir, existing_files, file_func_map)
    candidates = await discovery_agent.discover_bugs(bugged_dir, topics)
    print("Candidates JSON:", json.dumps(candidates, indent=2))

    # 2. Design bugs for each candidate
    design_agent = BugDesignAgent(model_client, bugged_dir)
    bug_plans = await design_agent.design_bugs(bugged_dir, candidates, topics)
    print("Bug plans:", json.dumps(bug_plans, indent=2))

    # 3. Add topic info and group bugs by topic
    bug_plans = add_topics_to_bugs(bug_plans, candidates)
    grouped_bugs = group_bugs_by_topic(bug_plans)
    print("Grouped bugs by topic:", json.dumps(grouped_bugs, indent=2))

    original_structure = extract_project_structure(bugged_dir)

    # 4. Agent-based selection of bugs to inject
    bug_selector = BugSelectionAgent(model_client)
    bugs_to_inject = await bug_selector.select_bugs(grouped_bugs)
    print("Selected bugs to inject:", json.dumps(bugs_to_inject, indent=2))

    # 5. Inject bugs and write manifests
    apply_bugs_and_write_manifests(bugged_dir, bugs_to_inject)
    modified_structure = extract_project_structure(bugged_dir)
    if not compare_structures(original_structure, modified_structure):
        print("Restoring skeletons for missing structures...")
        restore_skeletons(bugged_dir, original_structure)
    print(f"Bug-injected project and manifests are ready in {bugged_dir}")

    # 6. Critic/Feedback Agent (optional but recommended)
    with open(Path(bugged_dir) / "bug_manifest.json") as mf:
        bug_manifest = json.load(mf)
    with open(Path(bugged_dir) / "bug_hints.json") as hf:
        bug_hints = json.load(hf)
    critic_agent = CriticAgent(model_client, bugged_dir, existing_files)
    feedback = await critic_agent.provide_feedback(bugged_dir, bug_manifest, bug_hints)
    print("Feedback/Critique:", json.dumps(feedback, indent=2))


if __name__ == "__main__":
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    # Example usage: pass your unique_id and topic list
    asyncio.run(bug_injection_workflow(
        model_client,
        "2604b200-c1e0-45ad-bc9a-d74351e4465c",
    ["Dependency Injection", "Pydantic Model", "db connection", "Exception Handling"]
    ))
