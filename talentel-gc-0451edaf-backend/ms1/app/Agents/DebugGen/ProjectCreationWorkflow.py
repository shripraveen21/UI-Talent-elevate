import json
import os
import uuid
from pathlib import Path
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

# --- Agents with Improved Prompts ---
class BRDAgent:
    def __init__(self, model_client, project_dir):
        self.agent = AssistantAgent(
            name="brd_agent",
            model_client=model_client,
            system_message=f"""
You are a senior business analyst and software architect.

Your tasks:
1. Given a technology stack and initial topics, create a comprehensive Business Requirements Document (BRD) for a realistic mini-project.
2. Suggest additional topics/features that would make the project robust, practical, and educational. For each suggestion, explain briefly why it adds value.
3. Include in the BRD: project overview, user stories, acceptance criteria, assumptions, limitations, and a summary of why the suggested topics were added.

IMPORTANT:
- Output ONLY valid JSON. Do NOT include any code block markers (such as ```json), explanations, or extra text.
- Do NOT split the JSON across multiple messages. The output must be a single, valid JSON object matching this schema:
{{
    "brd": "BRD text here",
    "topics": ["topic1", "topic2", ...],
    "suggested_topics": [
        {{"topic": "additional1", "reason": "Why it's valuable"}},
        ...
    ]
}}
- If you do not follow this format exactly, your output will be discarded.

You have access to tools for reading and writing files and directories in the project folder: {project_dir}. Use these tools to inspect or update files if needed.
Do not include explanations, markdown, or extra text.

End with TERMINATE.
"""
        )

    async def generate_brd(self, tech_stack, topics, feedback=None):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Create a BRD for a mini-project using {tech_stack} covering these topics: {', '.join(topics)}.
Suggest any additional topics/features for completeness.
"""
        if feedback:
            task += f"\n\nIncorporate the following user feedback or corrections: {feedback}\n"
        result = await team.run(task=task)
        # Robustly parse only the first valid JSON object from agent output
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "brd_agent":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    continue
        raise ValueError("No valid JSON found in agent output")

def human_feedback_loop(brd_data):
    print("\n--- BRD & Topic Review ---")
    print("Business Requirements Document:\n", brd_data["brd"])
    print("Initial Topics:", brd_data["topics"])
    print("Suggested Additional Topics:")
    for item in brd_data["suggested_topics"]:
        print(f"- {item['topic']}: {item['reason']}")
    print("\nWould you like to add/remove topics? (y/n)")
    choice = input().strip().lower()
    if choice == "y":
        print("Enter final topic list, comma-separated:")
        final_topics = input().strip().split(",")
        final_topics = [t.strip() for t in final_topics if t.strip()]
    else:
        final_topics = brd_data["topics"] + [item["topic"] for item in brd_data["suggested_topics"]]
    return final_topics

class StructureAgent:
    def __init__(self, model_client, project_dir):
        self.agent = AssistantAgent(
            name="structure_agent",
            model_client=model_client,
            system_message=f"""
You are a software architect.
Your tasks:
1. Given a BRD and topic list, design a logical, maintainable file/directory structure for the mini-project.
2. Group files by responsibility (e.g., source code, tests, docs), and explain the rationale for your choices.
3. Output ONLY valid JSON:
{{
    "structure": {{
        "src": ["main.py", "utils.py"],
        "tests": ["test_main.py"],
        "docs": ["BRD.md", "README.md"]
    }},
    "rationale": {{
        "src": "Source code files implementing main logic.",
        "tests": "Unit and integration tests.",
        "docs": "Documentation and requirements."
    }}
}}
4. You have access to tools for reading, writing, and listing files/directories in {project_dir}. Use these tools to inspect or update files if needed.
Do not include explanations, markdown, or extra text.
End with TERMINATE.
"""
        )

    async def generate_structure(self, brd, topics):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Design a file/directory structure for a mini-project with BRD:\n{brd}\nTopics: {', '.join(topics)}
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "structure_agent":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        parsed = json.loads(json_content)
        return parsed["structure"], parsed["rationale"]

class CodeAgent:
    def __init__(self, model_client, project_dir):
        self.agent = AssistantAgent(
            name="code_agent",
            model_client=model_client,
            system_message=f"""
            You are a senior developer.

            Your tasks:
            1. Given a file/directory structure, BRD, and topic list, generate clean, working code for each file.
            2. Ensure the code is runnable as a complete project. Include all necessary configuration files (e.g., requirements.txt, .env.example).
            3. Add comments, docstrings, and basic error handling. Ensure code matches the BRD’s acceptance criteria.
            4. Generate basic unit tests and ensure they pass.
            5. If any file already exists in {project_dir}, use the tools to read it and avoid overwriting unless necessary.

            IMPORTANT:
            - Output ONLY valid JSON. Do NOT include any code block markers (such as ```json), explanations, or extra text.
            - Do NOT split the JSON across multiple messages. The output must be a single, valid JSON object matching this schema:
            {{
                "files": {{
                    "src/main.py": "# code here",
                    "src/utils.py": "# code here",
                    "tests/test_main.py": "# code here",
                    "docs/BRD.md": "# BRD text",
                    "docs/README.md": "# README text"
                }}
            }}
            - If you do not follow this format exactly, your output will be discarded.

            You have access to tools for reading, writing, and listing files/directories in {project_dir}. Use these tools to inspect or update files as needed.
            Do not include explanations, markdown, or extra text.

            End with TERMINATE.
            """

        )

    async def generate_code(self, structure, brd, topics):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Generate code for each file in this structure: {json.dumps(structure)}
BRD: {brd}
Topics: {', '.join(topics)}
"""
        result = await team.run(task=task)
        # Robustly parse only the first valid JSON object from agent output
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "code_agent":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                try:
                    return json.loads(content)["files"]
                except json.JSONDecodeError:
                    continue
        raise ValueError("No valid JSON found in agent output")

def write_project_files(base_path, files):
    Path(base_path).mkdir(parents=True, exist_ok=True)
    manifest = {}
    for rel_path, content in files.items():
        file_path = Path(base_path) / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        manifest[rel_path] = {"size": len(content)}
    # Write manifest
    with open(Path(base_path) / "manifest.json", 'w') as mf:
        json.dump(manifest, mf, indent=2)

import asyncio

async def agentic_workflow_1(tech_stack, initial_topics, model_client, unique_id=None):
    if unique_id is None:
        unique_id = str(uuid.uuid4())
    project_dir = f"GeneratedProject/{unique_id}/project"
    Path(project_dir).mkdir(parents=True, exist_ok=True)

    # 1. BRD + Topic Expansion
    brd_agent = BRDAgent(model_client, project_dir)
    brd_data = await brd_agent.generate_brd(tech_stack, initial_topics)

    # 2. Human Feedback Loop
    final_topics = human_feedback_loop(brd_data)
    brd_text = brd_data["brd"]

    # 3. Structure Agent
    structure_agent = StructureAgent(model_client, project_dir)
    structure, rationale = await structure_agent.generate_structure(brd_text, final_topics)

    # 4. Code Agent
    code_agent = CodeAgent(model_client, project_dir)
    files = await code_agent.generate_code(structure, brd_text, final_topics)

    # 5. Write files & manifest
    write_project_files(project_dir, files)
    print(f"Project files written to {project_dir}")
    print("Structure rationale:", json.dumps(rationale, indent=2))

if __name__ == "__main__":
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    asyncio.run(agentic_workflow_1("Python FastAPI", ["Dependency Injection", "Pydantic Model", "db connection", "Exception Handling"], model_client))
