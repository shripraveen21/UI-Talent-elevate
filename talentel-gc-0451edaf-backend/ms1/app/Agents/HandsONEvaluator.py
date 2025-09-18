import asyncio
import json
import os
import re

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from dotenv import load_dotenv

from .DebugGen.FSTool import FileSystemTool

load_dotenv()

# --- Safe JSON parsing ---
def safe_parse_agent_response(response):
    lines = response.splitlines()
    json_lines = []
    for line in lines:
        if line.strip().startswith("<|FileSystemTool|>"):
            continue
        if not line.strip():
            continue
        json_lines.append(line)
    response = "\n".join(json_lines).strip()
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()
    matches = re.findall(r'(\{.*\}|\[.*\])', response, re.DOTALL)
    if not matches:
        print("Raw agent response for debugging:\n", response)
        raise ValueError("No valid JSON found in response.")
    json_str = max(matches, key=len)
    try:
        return json.loads(json_str)
    except Exception as e:
        print("Failed to parse extracted JSON:", json_str)
        raise

# --- Agents ---
class RequirementsExtractionAgent:
    def __init__(self, model_client, read_file_tool, srs_path):
        self.agent = AssistantAgent(
            name="requirements_extractor",
            model_client=model_client,
            system_message=f"""
You are a requirements extraction agent.
You have access to FileSystemTool for all file operations.
Your job is to read the provided SRS.md and extract a list of milestones.
For each milestone, include:
- Milestone name
- Functional requirements
- Acceptance criteria
- Relevant risks

Use FileSystemTool.read_file(path) to read the SRS file.
Output ONLY valid JSON in this format:
[
  {{
    "milestone": "Milestone Name",
    "requirements": [...],
    "acceptance_criteria": [...],
    "risks": [...]
  }},
  ...
]
Do not include explanations, markdown, or extra text.

End your response with TERMINATE.
""",
            tools=[read_file_tool]
        )
        self.srs_path = srs_path

    async def extract(self):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"Use FileSystemTool.read_file to read '{self.srs_path}' and extract all milestones and requirements as described."
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "requirements_extractor":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        return safe_parse_agent_response(json_content)

class AssignmentParsingAgent:
    def __init__(self, model_client, read_file_tool, codebase_dir, readme_path, srs_path):
        self.agent = AssistantAgent(
            name="assignment_parser",
            model_client=model_client,
            system_message=f"""
You are an assignment parsing agent.
You have access to FileSystemTool for all file operations.
For each milestone, use FileSystemTool.read_file and FileSystemTool.list_dir to:
- Find relevant code files
- Extract docstrings
- Read documentation sections

Output ONLY valid JSON in this format:
{{
  "milestone_name": {{
    "files": [...],
    "docstrings": ["..."],
    "readme_section": "...",
    "srs_section": "..."
  }},
  ...
}}
Do not include explanations, markdown, or extra text.

End your response with TERMINATE.
""",
            tools=[read_file_tool]
        )
        self.codebase_dir = codebase_dir
        self.readme_path = readme_path
        self.srs_path = srs_path

    async def parse(self, milestones):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Given the codebase at '{self.codebase_dir}', README.md at '{self.readme_path}', and SRS.md at '{self.srs_path}', for each milestone, list:
- Relevant code files
- Presence and quality of docstrings
- Related documentation sections

Milestones: {json.dumps(milestones)}
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "assignment_parser":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        return safe_parse_agent_response(json_content)

class MilestoneEvaluationAgent:
    def __init__(self, model_client, read_file_tool):
        self.agent = AssistantAgent(
            name="milestone_evaluator",
            model_client=model_client,
            system_message="""
You are a milestone evaluation agent.
You have access to FileSystemTool for all file operations.
For each milestone, you will receive:
- Extracted requirements and acceptance criteria
- Assignment content: code files, docstrings, documentation

Evaluate the milestone for:
- Completeness (all required files and docs present)
- Clarity (docstrings and documentation quality)
- Readiness (structure and modularity)
- Documentation (README.md and SRS.md coverage)

STRICT SCORING INSTRUCTIONS:
- For each criterion (completeness, clarity, readiness, documentation), assign:
    - 10 ONLY if ALL requirements and acceptance criteria are fully met, with no omissions.
    - 0 if any required element is missing.
    - Around 5 if partially met (some requirements/criteria present, but not all).
- Do NOT give scores above 0 if milestone files, code, or documentation are missing.
- Do try to spread out the score as possible within the range according to the evaluation
- Be critical: If in doubt, score lower.

For each, rate 0-10 and provide a brief justification.

Output ONLY valid JSON in this format:
{
  "milestone": "Milestone Name",
  "assessment": "CORRECT" | "PARTIALLY_CORRECT" | "INCORRECT",
  "score": 0-10,
  "ratings": {
    "completeness": 0-10,
    "clarity": 0-10,
    "readiness": 0-10,
    "documentation": 0-10
  },
  "summary": "One-sentence summary.",
  "strengths": ["..."],
  "areas_for_improvement": ["..."],
  "next_steps": ["..."]
}
Do not include explanations, markdown, or extra text.

End your response with TERMINATE.
""",
            tools=[read_file_tool]
        )

    async def evaluate(self, milestone, assignment_content):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
        Milestone: {milestone['milestone']}
        Requirements: {json.dumps(milestone['requirements'])}
        Acceptance Criteria: {json.dumps(milestone['acceptance_criteria'])}
        Assignment Content: {json.dumps(assignment_content)}

        For scoring:
        - For completeness, check if EVERY requirement and acceptance criterion is satisfied in the assignment content.
        - If ANY are missing, score 0 for completeness.
        - Only score 10 if ALL are present and correct.
        - Be strict and do NOT give partial credit unless justified.

        Evaluate as described above.
        """

        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "milestone_evaluator":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        return safe_parse_agent_response(json_content)

# --- Aggregation ---
def aggregate_evaluations(milestone_evaluations):
    overall_score = round(sum([m["score"] for m in milestone_evaluations]) / len(milestone_evaluations), 2)
    overall_ratings = {
        "completeness": round(sum([m["ratings"]["completeness"] for m in milestone_evaluations]) / len(milestone_evaluations), 2),
        "clarity": round(sum([m["ratings"]["clarity"] for m in milestone_evaluations]) / len(milestone_evaluations), 2),
        "readiness": round(sum([m["ratings"]["readiness"] for m in milestone_evaluations]) / len(milestone_evaluations), 2),
        "documentation": round(sum([m["ratings"]["documentation"] for m in milestone_evaluations]) / len(milestone_evaluations), 2)
    }
    return {
        "overall_score": overall_score,
        "overall_ratings": overall_ratings,
        "milestone_evaluations": milestone_evaluations
    }

class MilestoneVerificationAgent:
    def __init__(self, model_client):
        self.agent = AssistantAgent(
            name="milestone_verifier",
            model_client=model_client,
            system_message="""
You are a milestone evaluation verifier.

You will receive:
- The milestone name, requirements, and acceptance criteria.
- Assignment content (files, docstrings, documentation).
- The initial evaluation (including all scores and justifications).

Your job:
- Critically check if the evaluation is justified and strictly follows the rubric.
- If any requirement or acceptance criterion is missing but the score is above 0, flag this as an error.
- If the evaluation is too lenient or inconsistent, suggest corrected scores and justifications.
- If the evaluation is correct, approve it.

Output ONLY valid JSON in this format:
{
  "verdict": "APPROVED" | "REVISE",
  "corrected_evaluation": { ... },  # Only include if "REVISE"
  "comments": ["..."]               # Brief comments on your decision
}
Do not include explanations, markdown, or extra text.

End your response with TERMINATE.
"""
        )

    async def verify(self, milestone, assignment_content, evaluation):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Milestone: {milestone['milestone']}
Requirements: {json.dumps(milestone['requirements'])}
Acceptance Criteria: {json.dumps(milestone['acceptance_criteria'])}
Assignment Content: {json.dumps(assignment_content)}
Initial Evaluation: {json.dumps(evaluation)}

Check if the evaluation strictly follows the rubric and is justified.
If not, suggest corrections.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "milestone_verifier":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        return safe_parse_agent_response(json_content)

# --- Main Workflow (with verification) ---

async def agentic_assignment_evaluation_workflow(
    srs_path,
    readme_path,
    codebase_dir,
    model_client
):
    file_tool = FileSystemTool

    # 1. Extract milestones from SRS.md
    requirements_agent = RequirementsExtractionAgent(model_client, file_tool, srs_path)
    milestones = await requirements_agent.extract()

    # 2. Parse assignment codebase and docs
    parsing_agent = AssignmentParsingAgent(model_client, file_tool, codebase_dir, readme_path, srs_path)
    assignment_content = await parsing_agent.parse(milestones)

    # 3. Evaluate and verify each milestone
    evaluation_agent = MilestoneEvaluationAgent(model_client, file_tool)
    verification_agent = MilestoneVerificationAgent(model_client)
    milestone_evaluations = []

    for milestone in milestones:
        milestone_name = milestone["milestone"]
        assignment_info = assignment_content.get(milestone_name, {})
        eval_result = await evaluation_agent.evaluate(milestone, assignment_info)
        verify_result = await verification_agent.verify(milestone, assignment_info, eval_result)

        # Use corrected evaluation if needed
        if verify_result.get("verdict") == "REVISE" and "corrected_evaluation" in verify_result:
            print(f"Verifier revised evaluation for '{milestone_name}': {verify_result.get('comments', [])}")
            milestone_evaluations.append(verify_result["corrected_evaluation"])
        else:
            milestone_evaluations.append(eval_result)

    # 4. Aggregate and report
    report = aggregate_evaluations(milestone_evaluations)
    print(json.dumps(report, indent=2))
    return report

# --- Usage Example ---

if __name__ == "__main__":
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )

    project_path = os.getenv("PROJECT_PATH", "GeneratedHandsON")
    user_path = os.getenv("USER_PATH", "UserST")
    asyncio.run(agentic_assignment_evaluation_workflow(
        srs_path=f"{project_path}/3c9da814-2b9d-44f3-9aad-d4f5c3628591/SRS.md",
        readme_path=f"{project_path}/3c9da814-2b9d-44f3-9aad-d4f5c3628591/README.md",
        codebase_dir=f"{user_path}/3c9da814-2b9d-44f3-9aad-d4f5c3628591/project",
        model_client=model_client
    ))
