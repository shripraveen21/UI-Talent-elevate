import asyncio
import json
import os
import re
import difflib

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from dotenv import load_dotenv

from .FSTool import FileSystemTool

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

# --- Code Diff Utility ---
def compute_code_diff(original_code, user_code):
    original_lines = original_code.splitlines()
    user_lines = user_code.splitlines()
    diff = list(difflib.unified_diff(original_lines, user_lines, lineterm=''))
    return diff

# --- Agents ---
class CodeExtractionAgent:
    def __init__(self, model_client, codebase_dir, read_file_tool):
        self.agent = AssistantAgent(
            name="code_extractor",
            model_client=model_client,
            system_message=f"""
You are a code extraction agent. 
Your job is to extract the full code block (function or class definition) from files in {codebase_dir} using the FileSystemTool.

Instructions:
- You will be given a file path and a location (function or class name).
- Use FileSystemTool.read_file to read the file.
- Locate and extract the entire code block for the specified location.
- Only return the code block, not the entire file.

Output ONLY valid JSON in this format:
{{
    "code_block": "<full code block as a string>"
}}
Do not include explanations, markdown, or extra text.

End your response with TERMINATE.
""",
            tools=[read_file_tool]
        )

    async def extract_code(self, file_path, location):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Use FileSystemTool.read_file to read '{file_path}' and extract the code block for '{location}'.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "code_extractor":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        obj = safe_parse_agent_response(json_content)
        return obj.get("code_block", "")

class BugManifestExplicatorAgent:
    def __init__(self, model_client):
        self.agent = AssistantAgent(
            name="manifest_explicator",
            model_client=model_client,
            system_message="""
            You are a bug manifest explicator.

            You will receive a bug manifest entry describing a code bug.

            Your job:
            - Summarize the bug in broad, actionable terms that apply to similar bugs or coding situations.
            - Explain what a correct fix should accomplish, not just for this instance but for similar problems in general.
            - List common mistakes and edge cases relevant to this bug type or topic, including those seen in related bugs or code patterns.
            - Provide a checklist of broader principles and steps to confirm the bug is fixed, which could help in reviewing similar code in the future.

            **Be comprehensive and general in your output. Favor broader patterns and best practices over narrow specifics.**

            Output ONLY valid JSON:
            {
                "bug_summary": "Broad, actionable summary of the bug and its context.",
                "expected_fix": "General description of what a correct fix should do for this bug type.",
                "common_mistakes": ["Mistake 1 (general)", "Mistake 2 (general)", ...],
                "checklist": ["Broad review step 1", "Broad review step 2", ...]
            }
            Do not include explanations, markdown, or extra text.
            End your response with TERMINATE.
            """
        )

    async def explicate(self, bug_info):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Bug Manifest Entry:
{json.dumps(bug_info, indent=2)}
Explicate as described above.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "manifest_explicator":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        obj = safe_parse_agent_response(json_content)
        return obj

class BugEvaluationAgent:
    def __init__(self, model_client, read_file_tool):
        self.agent = AssistantAgent(
            name="bug_evaluator",
            model_client=model_client,
            system_message="""
            You are a senior debugging evaluator.

            You will receive:
            - Buggy code (with an injected bug)
            - Original code (correct version)
            - User-fixed code (learner's attempt)
            - Bug Manifest entry (details about the injected bug)
            - Bug manifest explication (summary, expected fix, common mistakes, checklist)
            - Code diff between original and user-fixed code

            Your job is to evaluate the user-fixed code using these criteria:

            1. Does the solution fix the identified bug described in the bug manifest?
            2. Will the code actually work as intended? Reason about the runtime behavior.
            3. Are any new bugs introduced?
            4. Is the code clean, readable, and following best practices?

            **Instructions:**
            - Use only the information in the bug manifest, manifest explication, and the provided code. Do NOT make assumptions not supported by the code or manifest.
            - Provide a concise summary (max 2 sentences, direct language) of the overall evaluation.
            - List up to 2 strengths, focusing ONLY on aspects directly relevant to the bug topic (not generic code structure, syntax, or style unless the bug is about those).
            - List up to 2 areas for improvement, focusing on what prevents the solution from being fully correct or robust.

            **Assessment and scoring rules:**
            - Only mark "CORRECT" and score 1 if the user-fixed code fully resolves the bug, introduces no new issues, and addresses all relevant checklist items with no mistakes.
            - Mark "PARTIALLY_CORRECT" and score 0.2 if the fix is incomplete, introduces minor issues, or if you are uncertain about full correctness.
            - Mark "INCORRECT" and score 0 if the fix does not resolve the bug or introduces significant new issues.

            **Output ONLY valid JSON in this format:**
            {
                "assessment": "CORRECT" | "PARTIALLY_CORRECT" | "INCORRECT",
                "score": 1 | 0.2 | 0,
                "summary": "A concise summary of the overall evaluation (max 2 sentences, direct language).",
                "strengths": ["Max 2 strengths, only if relevant to the bug topic."],
                "areas_for_improvement": ["Max 2 areas for improvement, only if relevant to the bug topic."],
                "topic": "<main topic for this bug>"
            }
            Do not include explanations, markdown, differences, justification, or manifest explicator in your output.
            End your response with TERMINATE.
            """
            ,
            tools=[read_file_tool]
        )

    async def evaluate_bug(self, bug_info, buggy_code, original_code, user_code, code_diff, explicator_output):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Bug Manifest: {json.dumps(bug_info, indent=2)}
Bug Manifest Explication: {json.dumps(explicator_output, indent=2)}
Buggy Code:
{buggy_code}
Original Code:
{original_code}
User-Fixed Code:
{user_code}
Code Diff:
{json.dumps(code_diff, indent=2)}
Evaluate the user-fixed code as described above.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "bug_evaluator":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        obj = safe_parse_agent_response(json_content)
        return obj

class CriticAgent:
    def __init__(self, model_client):
        self.agent = AssistantAgent(
            name="critic_agent",
            model_client=model_client,
            system_message="""
            You are a strict critical code review agent.

            You will receive:
            - Bug manifest entry
            - Bug manifest explication (summary, expected fix, common mistakes, checklist)
            - Buggy code
            - Original code
            - User-fixed code
            - Code diff between original and user-fixed code
            - Initial evaluation (including assessment, score, summary, strengths, areas_for_improvement)

            **Your job:**
            - Review the initial evaluation and all provided information with a critical, high standard.
            - Only mark "CORRECT" and score 1 if the user-fixed code fully resolves the bug, covers every relevant checklist item, and introduces no new issues or omissions—even minor ones.
            - If there are any mistakes, omissions, or unaddressed checklist items, mark as "PARTIALLY_CORRECT" (score 0.2) or "INCORRECT" (score 0), and clearly state the reasons in areas_for_improvement.
            - Do not give strengths for generic code quality, structure, or syntax unless the bug is explicitly about those topics.
            - Always be explicit and direct in your summary and feedback.
            - If you find inconsistencies between assessment and score, correct them and explain in areas_for_improvement.
            - Output ONLY the assessment, score, summary, strengths, and areas_for_improvement for the user.
            - Do not include explanations, markdown, differences, justification, or manifest explicator in your output.
            - Do NOT make assumptions not supported by the code or manifest.

            **Output ONLY valid JSON:**
            {
                "critic_assessment": "CORRECT" | "PARTIALLY_CORRECT" | "INCORRECT",
                "critic_score": 1 | 0.2 | 0,
                "summary": "A concise summary of the overall evaluation (max 2 sentences, direct language).",
                "strengths": ["Max 2 strengths, only if relevant to the bug topic."],
                "areas_for_improvement": ["Max 2 areas for improvement, only if relevant to the bug topic, and always include any missed checklist items or minor mistakes."]
            }
            End your response with TERMINATE.
            """
        )

    async def review_bug(self, bug_info, buggy_code, original_code, user_code, code_diff, initial_evaluation, explicator_output):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Bug Manifest: {json.dumps(bug_info, indent=2)}
Bug Manifest Explication: {json.dumps(explicator_output, indent=2)}
Buggy Code:
{buggy_code}
Original Code:
{original_code}
User-Fixed Code:
{user_code}
Code Diff:
{json.dumps(code_diff, indent=2)}
Initial Evaluation:
{json.dumps(initial_evaluation, indent=2)}
Critically review the initial evaluation as described above.
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

# --- Main Workflow ---
async def agentic_debug_evaluation_workflow(
    bug_manifest_path,
    bugged_dir,
    original_dir,
    user_dir,
    model_client,
    partial_weight=0.2
):
    # 1. Load bug manifest
    with open(bug_manifest_path) as f:
        bug_manifest = json.load(f)

    # 2. Initialize FileSystemTool
    file_tool = FileSystemTool

    # 3. Initialize Agents
    buggy_extractor = CodeExtractionAgent(model_client, bugged_dir, file_tool)
    original_extractor = CodeExtractionAgent(model_client, original_dir, file_tool)
    user_extractor = CodeExtractionAgent(model_client, user_dir, file_tool)
    manifest_explicator = BugManifestExplicatorAgent(model_client)
    bug_evaluator = BugEvaluationAgent(model_client, file_tool)
    critic_agent = CriticAgent(model_client)

    user_report = []

    # 4. For each bug, extract code and evaluate
    for bug_id, bug in bug_manifest.items():
        file_path = bug['file']
        location = bug['location']
        buggy_code = await buggy_extractor.extract_code(file_path, location)
        original_code = await original_extractor.extract_code(file_path, location)
        user_code = await user_extractor.extract_code(file_path, location)
        code_diff = compute_code_diff(original_code, user_code)

        bug_info = {
            "id": bug_id,
            "file": file_path,
            "location": location,
            "type": bug.get("type", ""),
            "description": bug.get("description", ""),
            "hint": bug.get("hint", "")
        }

        # 1. Manifest explication (for agent context only)
        explicator_output = await manifest_explicator.explicate(bug_info)

        # 2. Primary evaluation
        evaluation = await bug_evaluator.evaluate_bug(
            bug_info, buggy_code, original_code, user_code, code_diff, explicator_output
        )

        # 3. Critic review
        critic_evaluation = await critic_agent.review_bug(
            bug_info, buggy_code, original_code, user_code, code_diff, evaluation, explicator_output
        )

        # 4. Build user-facing report (exclude justification, differences, manifest explicator)
        user_report.append({
            "id": bug_id,
            "topic": bug.get("type", ""),
            "assessment": critic_evaluation.get("critic_assessment", evaluation.get("assessment")),
            "score": critic_evaluation.get("critic_score", evaluation.get("score")),
            "summary": critic_evaluation.get("summary", evaluation.get("summary")),
            "strengths": critic_evaluation.get("strengths", evaluation.get("strengths")),
            "areas_for_improvement": critic_evaluation.get("areas_for_improvement",
                                                           evaluation.get("areas_for_improvement"))
        })

    # 5. Final user-facing report
    print(json.dumps(user_report, indent=2))
    return user_report

if __name__ == "__main__":
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    asyncio.run(agentic_debug_evaluation_workflow(
        bug_manifest_path="BugInjectedProject/7e0e2a9e-8fda-4816-8492-926f41520a91/project/bug_manifest.json",
        bugged_dir="BugInjectedProject/7e0e2a9e-8fda-4816-8492-926f41520a91/project",
        original_dir="GeneratedProject/7e0e2a9e-8fda-4816-8492-926f41520a91/project",
        user_dir="UserST/7e0e2a9e-8fda-4816-8492-926f41520a91/project",
        model_client=model_client,
        partial_weight=0.2  # You can adjust partial credit here
    ))
