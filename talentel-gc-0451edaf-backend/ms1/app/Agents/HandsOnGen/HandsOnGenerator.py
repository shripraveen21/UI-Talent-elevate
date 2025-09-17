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

class FileSystemTool:
    @staticmethod
    def write_file(file_path, content):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

# --- Assignment Agent ---
class AssignmentAgent:
    def __init__(self, model_client, project_dir, tool):
        self.agent = AssistantAgent(
            name="assignment_agent",
            model_client=model_client,
            tools=[tool],
            system_message="""
            You are a senior instructor.

            Your tasks:
            1. Given a project name, context, and requirements, create an assignment in Markdown format.
            2. The assignment should summarize the project, objectives, required deliverables (SRS.md, README.md, boilerplate code files), and provide clear instructions for the assignee.
            3. Output only valid Markdown suitable for saving as ASSIGNMENT.md.

            End with TERMINATE.
            """
        )

    async def generate_assignment(self, project_name, srs_md):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Create an assignment for the project "{project_name}" based on the following requirements document:

{srs_md}

List the required deliverables: SRS.md, README.md, boilerplate code files. Provide instructions for the assignee.
"""
        result = await team.run(task=task)
        md_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "assignment_agent":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```markdown") and content.endswith("```"):
                    content = content[10:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                md_content += content
        return md_content

# --- Requirements Agent ---
class RequirementsAgent:
    def __init__(self, model_client, project_dir, tool):
        self.agent = AssistantAgent(
            name="requirements_agent",
            model_client=model_client,
            tools=[tool],
            system_message="""
            You are a senior product and systems analyst.

            Your tasks:
            1. Given a project name, business context, and initial topics or goals, generate a detailed Software Requirements Specification (SRS) for the project in Markdown format.
            2. Organize the SRS by milestones or feature groups. For each, specify:
               - Milestone/feature name and description
               - Functional requirements (detailed, but not technical implementation)
               - User roles and permissions
               - Business rules and logic
               - User stories/scenarios
               - Acceptance criteria
               - Assumptions and constraints
               - Risks and mitigation strategies
               - High-level solution context (integrations, data flows, non-functional requirements)
            3. Include an introduction, stakeholder summary, and a summary table of all milestones/features.
            4. Output ONLY valid Markdown, suitable for saving as a `.md` file.

            End with TERMINATE.
            """
        )

    async def generate_srs(self, tech_stack, topics):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Create a detailed SRS in Markdown for a project using {tech_stack} covering these topics: {', '.join(topics)}.
Suggest any additional topics/features for completeness.
"""
        result = await team.run(task=task)
        md_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "requirements_agent":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```markdown") and content.endswith("```"):
                    content = content[10:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                md_content += content
        return md_content

# --- README Agent ---
class ReadmeAgent:
    def __init__(self, model_client, project_dir, tool):
        self.agent = AssistantAgent(
            name="readme_agent",
            model_client=model_client,
            tools=[tool],
            system_message="""
            You are a software architect.

            Your tasks:
            1. Given a Software Requirements Specification (SRS) in Markdown, generate a README.md in Markdown format.
            2. The README should summarize the project, list milestones/features, and provide setup instructions for a new user.
            3. Output ONLY valid Markdown suitable for saving as README.md.

            End with TERMINATE.
            """
        )

    async def generate_readme(self, srs_md):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Create a README.md in Markdown for the following project SRS:

{srs_md}
"""
        result = await team.run(task=task)
        md_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "readme_agent":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```markdown") and content.endswith("```"):
                    content = content[10:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                md_content += content
        return md_content

# --- Boilerplate Agent ---
class BoilerplateAgent:
    def __init__(self, model_client, project_dir, tool, tech_stack):
        self.agent = AssistantAgent(
            name="boilerplate_agent",
            model_client=model_client,
            tools=[tool],
            system_message=f"""
            You are a backend engineer.

            Your task:
            1. Given the SRS in Markdown, generate the most minimal runnable boilerplate code for a {tech_stack} project.
            2. For FastAPI, output only:
                - main.py: initializes the FastAPI app and provides a single GET / endpoint returning 'Hello, World!'
                - requirements.txt: lists FastAPI with a specific version.
            3. Output each file as a Markdown code block with the filename as a heading (e.g., ### main.py), followed by the code.
            4. Do not include any other files, endpoints, or business logic.

            End with TERMINATE.
            """
        )

    async def generate_boilerplate(self, srs_md):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Given the following SRS, generate the minimal boilerplate codebase as described.

{srs_md}
"""
        result = await team.run(task=task)
        files = {}
        current_file = None
        code_lines = []
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "boilerplate_agent":
                content = message.content.replace("TERMINATE", "").strip()
                lines = content.splitlines()
                for line in lines:
                    if line.startswith("### "):
                        if current_file and code_lines:
                            files[current_file] = "\n".join(code_lines).strip()
                            code_lines = []
                        current_file = line.replace("### ", "").strip()
                    elif line.startswith("```") and not code_lines:
                        continue
                    elif line.startswith("```") and code_lines:
                        continue
                    else:
                        if current_file:
                            code_lines.append(line)
                if current_file and code_lines:
                    files[current_file] = "\n".join(code_lines).strip()
        return files


import asyncio

async def agentic_workflow(project_name, tech_stack, initial_topics, model_client, unique_id=None):
    if unique_id is None:
        unique_id = str(uuid.uuid4())
    output_dir = os.getenv("HANDSON_DIR", "GeneratedHandsON")
    project_dir = f"{output_dir}/{unique_id}/project"
    Path(project_dir).mkdir(parents=True, exist_ok=True)

    tool = FileSystemTool

    # 1. SRS Generation
    requirements_agent = RequirementsAgent(model_client, project_dir, tool)
    srs_md = await requirements_agent.generate_srs(tech_stack, initial_topics)
    srs_path = Path(project_dir) / "SRS.md"
    tool.write_file(srs_path, srs_md)

    # 2. Assignment Generation
    assignment_agent = AssignmentAgent(model_client, project_dir, tool)
    assignment_md = await assignment_agent.generate_assignment(project_name, srs_md)
    assignment_path = Path(project_dir) / "ASSIGNMENT.md"
    tool.write_file(assignment_path, assignment_md)

    # 3. README Generation
    readme_agent = ReadmeAgent(model_client, project_dir, tool)
    readme_md = await readme_agent.generate_readme(srs_md)
    readme_path = Path(project_dir) / "README.md"
    tool.write_file(readme_path, readme_md)

    # 4. Boilerplate Code Generation
    boilerplate_agent = BoilerplateAgent(model_client, project_dir, tool, tech_stack)
    files = await boilerplate_agent.generate_boilerplate(srs_md)
    for filename, code in files.items():
        file_path = Path(project_dir) / filename
        tool.write_file(file_path, code)
        print(f"Generated: {file_path}")

    print(f"\nAssignment, SRS, README, and boilerplate codebase saved to: {project_dir}")

if __name__ == "__main__":
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    asyncio.run(agentic_workflow(
        "HashedIn Research Platform",
        "Python FastAPI",
        ["User Authentication", "Profile Management", "Points System", "Research Paper Upload", "Chat System", "Filtering & Search", "API Documentation", "Testing", "Deployment"],
        model_client
    ))
