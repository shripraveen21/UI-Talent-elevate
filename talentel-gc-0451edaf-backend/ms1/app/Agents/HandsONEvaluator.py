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

# --- Utility: Robust JSON Parsing ---
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
    # Try parsing as array
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try splitting multiple objects
        objects = re.findall(r'(\{.*?\})(?=\s*\{|\s*$)', response, re.DOTALL)
        if objects:
            return [json.loads(obj) for obj in objects]
        print("Raw agent response for debugging:\n", response)
        raise ValueError("No valid JSON found in response.")

def read_file_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# --- Unified Agent: Requirement Extraction + Assignment Parsing ---
class MilestoneAnalysisAgent:
    def __init__(self, model_client, codebase_dir, readme_path):
        self.agent = AssistantAgent(
            name="milestone_analyzer",
            model_client=model_client,
            system_message=f"""
You are a milestone analysis agent for software engineering assignments.

Instructions:
- You will receive the full SRS markdown text, the codebase directory path, and the README.md path.
- Parse the SRS markdown to identify all milestones (e.g., '### Milestone X: ...').
- For each milestone, extract:
    - Milestone name
    - Functional requirements
    - Acceptance criteria
    - Relevant risks
- For each milestone, analyze the codebase and documentation:
    - List relevant code files
    - Extract docstrings from those files
    - Summarize related sections from README.md and SRS.md

Output ONLY valid JSON in this format:
[
  {{
    "milestone": "Milestone Name",
    "requirements": [...],
    "acceptance_criteria": [...],
    "risks": [...],
    "files": [...],
    "docstrings": ["..."],
    "readme_section": "...",
    "srs_section": "..."
  }},
  ...
]
Do not include explanations, markdown, or extra text.

End your response with TERMINATE.
"""
            ,
            tools=[FileSystemTool]
        )
        self.codebase_dir = codebase_dir
        self.readme_path = readme_path

    async def analyze(self, srs_text):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = (
            f"Given the following SRS markdown:\n\n{srs_text}\n\n"
            f"and the codebase at '{self.codebase_dir}' and README.md at '{self.readme_path}', "
            "extract all milestones and for each, analyze the codebase and documentation as described."
        )
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "milestone_analyzer":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        return safe_parse_agent_response(json_content)

# --- Evaluation Agent ---
class MilestoneEvaluationAgent:
    def __init__(self, model_client):
        self.agent = AssistantAgent(
            name="milestone_evaluator",
            model_client=model_client,
            system_message="""
You are a milestone evaluation agent.

For each milestone, you will receive:
- Extracted requirements and acceptance criteria
- Assignment content: code files, docstrings, documentation

Evaluate the milestone for:
- Completeness (all required files and docs present)
- Clarity (docstrings and documentation quality)
- Readiness (structure and modularity)
- Documentation (coverage and usefulness)

STRICT SCORING INSTRUCTIONS:
- For each criterion (completeness, clarity, readiness, documentation), assign:
    - 10 ONLY if ALL requirements and acceptance criteria are fully met, with no omissions.
    - 0 if any required element is missing.
    - Around 5 if partially met (some requirements/criteria present, but not all).
- Do NOT give scores above 0 if milestone files, code, or documentation are missing.
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
"""
        )

    async def evaluate(self, milestone):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = (
            f"Milestone: {milestone['milestone']}\n"
            f"Requirements: {json.dumps(milestone['requirements'])}\n"
            f"Acceptance Criteria: {json.dumps(milestone['acceptance_criteria'])}\n"
            f"Assignment Content: {json.dumps({k: milestone[k] for k in ['files','docstrings','readme_section','srs_section']})}\n"
            "Evaluate as described above."
        )
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

# --- Verification Agent ---
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

    async def verify(self, milestone, evaluation):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = (
            f"Milestone: {milestone['milestone']}\n"
            f"Requirements: {json.dumps(milestone['requirements'])}\n"
            f"Acceptance Criteria: {json.dumps(milestone['acceptance_criteria'])}\n"
            f"Assignment Content: {json.dumps({k: milestone[k] for k in ['files','docstrings','readme_section','srs_section']})}\n"
            f"Initial Evaluation: {json.dumps(evaluation)}\n"
            "Check if the evaluation strictly follows the rubric and is justified. If not, suggest corrections."
        )
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

# --- Aggregation ---
def aggregate_evaluations(milestone_evaluations):
    if not milestone_evaluations:
        return {"overall_score": 0, "overall_ratings": {}, "milestone_evaluations": []}
    # Defensive: skip non-dict entries
    milestone_evaluations = [m for m in milestone_evaluations if isinstance(m, dict)]
    if not milestone_evaluations:
        return {"overall_score": 0, "overall_ratings": {}, "milestone_evaluations": []}
    overall_score = round(sum([m["score"] for m in milestone_evaluations]) / len(milestone_evaluations), 2)
    keys = milestone_evaluations[0]["ratings"].keys()
    overall_ratings = {
        k: round(sum([m["ratings"][k] for m in milestone_evaluations]) / len(milestone_evaluations), 2)
        for k in keys
    }
    return {
        "overall_score": overall_score,
        "overall_ratings": overall_ratings,
        "milestone_evaluations": milestone_evaluations
    }

# --- Main Workflow ---
async def agentic_assignment_evaluation_workflow(
    srs_path,
    readme_path,
    codebase_dir,
    model_client
):
    # 1. Read SRS text once
    srs_text = read_file_text(srs_path)
    analysis_agent = MilestoneAnalysisAgent(model_client, codebase_dir, readme_path)
    milestones = await analysis_agent.analyze(srs_text)

    # 2. Evaluate and verify each milestone in parallel
    evaluation_agent = MilestoneEvaluationAgent(model_client)
    verification_agent = MilestoneVerificationAgent(model_client)

    async def eval_and_verify(milestone):
        eval_result = await evaluation_agent.evaluate(milestone)
        verify_result = await verification_agent.verify(milestone, eval_result)
        if verify_result.get("verdict") == "REVISE" and "corrected_evaluation" in verify_result:
            print(f"Verifier revised evaluation for '{milestone['milestone']}': {verify_result.get('comments', [])}")
            return verify_result["corrected_evaluation"]
        else:
            return eval_result

    milestone_evaluations = await asyncio.gather(
        *(eval_and_verify(milestone) for milestone in milestones)
    )

    # 3. Aggregate and report
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
        srs_path=f"{project_path}/3c9da814-2b9d-44f3-9aad-d4f5c3628591/project/SRS.md",
        readme_path=f"{project_path}/3c9da814-2b9d-44f3-9aad-d4f5c3628591/project/README.md",
        codebase_dir=f"{user_path}/3c9da814-2b9d-44f3-9aad-d4f5c3628591/project",
        model_client=model_client
    ))
