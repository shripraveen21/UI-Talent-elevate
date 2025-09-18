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

Your job is to evaluate the user-fixed code using these criteria:

1. Correctness:
   - Does the solution fix the identified bug?
   - Are any new bugs introduced?
   - Does the code work as expected, including edge cases?
2. Completeness:
   - Are all aspects of the problem addressed?
   - Is the solution comprehensive?
   - Are all bugs in the original code fixed?
3. Quality:
   - Is the code clean and readable?
   - Are best practices followed?
   - Is the solution efficient and maintainable?
4. Alternative Solutions:
   - Are there other valid approaches?
   - What are the trade-offs?
   - Which solution is best and why?

You will evaluate the bugs based on the bug_manifest.json which has the injected bugs details
For each criterion, provide a rating (0-10) and a brief justification in the "details" section.

Output ONLY valid JSON in this format:
{
    "assessment": "CORRECT" | "PARTIALLY_CORRECT" | "INCORRECT",
    "score": 0-100,
    "ratings": {
        "correctness": 0-10,
        "completeness": 0-10,
        "quality": 0-10,
        "alternatives": 0-10
    },
    "summary": "A concise summary of the overall evaluation (max 2 sentences, direct language).",
    "strengths": ["Max 2 strengths."],
    "areas_for_improvement": ["Max 2 areas for improvement."],
    "next_steps": ["Max 2 actionable next steps."],
    "topic": "<main topic for this bug>"
}
Do not include explanations, markdown, or extra text.
End your response with TERMINATE.
""",
            tools=[read_file_tool]
        )

    async def evaluate_bug(self, bug_info, buggy_code, original_code, user_code):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Bug Info: {json.dumps(bug_info)}
Buggy Code:
{buggy_code}
Original Code:
{original_code}
User-Fixed Code:
{user_code}
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

class ResourceRecommendationAgent:
    def __init__(self, model_client):
        self.agent = AssistantAgent(
            name="resource_recommender",
            model_client=model_client,
            system_message="""
You are an educational resource recommender.

You will receive a list of topics.

For each, recommend 1-2 high-quality learning resources. For each resource, provide:
- Title
- URL

Output ONLY valid JSON in this format:
{
  "resources": [
    {
      "topic": "Topic Name",
      "recommendations": [
        {
          "title": "Resource Title",
          "url": "https://example.com/resource"
        }
      ]
    }
  ]
}
Do not include explanations, markdown, or extra text.
End your response with TERMINATE.
"""
        )

    async def recommend(self, topics):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.agent], termination_condition=termination)
        task = f"""
Here are the topics:
{json.dumps(topics, indent=2)}
Recommend resources as described above.
"""
        result = await team.run(task=task)
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "resource_recommender":
                content = message.content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        obj = safe_parse_agent_response(json_content)
        return obj.get("resources", [])

# --- Overall Score and Ratings Calculation ---
def calculate_overall_score_and_ratings(bug_results):
    total_score = 0
    ratings_sum = {"correctness": 0, "completeness": 0, "quality": 0, "alternatives": 0}
    count = len(bug_results)
    for bug in bug_results.values():
        total_score += bug.get("score", 0)
        for key in ratings_sum:
            ratings_sum[key] += bug.get("ratings", {}).get(key, 0)
    overall_score = round(total_score / count, 2) if count else 0
    overall_ratings = {k: round(v / count, 2) if count else 0 for k, v in ratings_sum.items()}
    return overall_score, overall_ratings

# --- Merge resources into bug results ---
def filter_resources_for_topic(resources, topic):
    for entry in resources:
        if topic.lower() in entry.get("topic", "").lower():
            return entry.get("recommendations", [])[:2]
    return []

def concise_bug_feedback(bug, resources):
    return {
        "bug_id": bug["id"],
        "topic": bug["topic"],
        "assessment": bug["assessment"],
        "score": bug["score"],
        "ratings": bug["ratings"],
        "summary": bug.get("summary", "")[:160],
        "strengths": bug.get("strengths", [])[:2],
        "areas_for_improvement": bug.get("areas_for_improvement", [])[:2],
        "next_steps": bug.get("next_steps", [])[:2],
        "resources": filter_resources_for_topic(resources, bug["topic"])
    }

def format_final_report(overall_score, overall_ratings, bug_evaluations, resources):
    final_bug_results = [
        concise_bug_feedback(bug, resources)
        for bug in bug_evaluations
    ]
    return {
        "overall_evaluation": {
            "overall_score": overall_score,
            "overall_ratings": overall_ratings,
            "summary": "See bug-wise details below."
        },
        "bug_wise_results": final_bug_results
    }

# --- Main Workflow ---
async def agentic_debug_evaluation_workflow(
    bug_manifest_path,
    bugged_dir,
    original_dir,
    user_dir,
    model_client
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
    bug_evaluator = BugEvaluationAgent(model_client, file_tool)
    resource_agent = ResourceRecommendationAgent(model_client)

    results = {}
    bug_evaluations = []

    # 4. For each bug, extract code and evaluate
    for bug_id, bug in bug_manifest.items():
        file_path = bug['file']
        location = bug['location']
        buggy_code = await buggy_extractor.extract_code(file_path, location)
        original_code = await original_extractor.extract_code(file_path, location)
        user_code = await user_extractor.extract_code(file_path, location)

        bug_info = {
            "id": bug_id,
            "file": file_path,
            "location": location,
            "type": bug.get("type", ""),
            "topic": bug.get("topic", ""),
            "description": bug.get("description", ""),
            "hint": bug.get("hint", "")
        }

        evaluation = await bug_evaluator.evaluate_bug(
            bug_info, buggy_code, original_code, user_code
        )
        results[bug_id] = evaluation
        bug_evaluations.append({
            "id": bug_id,
            "topic": evaluation.get("topic", bug_info["topic"]),
            "assessment": evaluation.get("assessment", ""),
            "score": evaluation.get("score", 0),
            "ratings": evaluation.get("ratings", {}),
            "summary": evaluation.get("summary", ""),
            "strengths": evaluation.get("strengths", []),
            "areas_for_improvement": evaluation.get("areas_for_improvement", []),
            "next_steps": evaluation.get("next_steps", [])
        })

    # 5. Calculate overall score/ratings
    overall_score, overall_ratings = calculate_overall_score_and_ratings(results)

    # 6. Gather all unique topics for resource recommendations
    unique_topics = list({bug["topic"] for bug in bug_evaluations if bug["topic"]})

    # 7. Resource recommendations (merged per bug)
    resources = await resource_agent.recommend(unique_topics)

    # 8. Final report (concise, merged)
    final_report = format_final_report(overall_score, overall_ratings, bug_evaluations, resources)
    # with open("final_debug_evaluation_report.json", "w") as f:
    #     json.dump(final_report, f, indent=2)
    print(json.dumps(final_report, indent=2))
    return final_report

if __name__ == "__main__":
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    asyncio.run(agentic_debug_evaluation_workflow(
        bug_manifest_path="BugInjectedProject/ce4abd9b-aa70-4e72-b8ff-c153b568f2ef/project/bug_manifest.json",
        bugged_dir="BugInjectedProject/ce4abd9b-aa70-4e72-b8ff-c153b568f2ef/project",
        original_dir="GeneratedProject/ce4abd9b-aa70-4e72-b8ff-c153b568f2ef/project",
        user_dir="UserFixedProject/ce4abd9b-aa70-4e72-b8ff-c153b568f2ef/project",
        model_client=model_client
    ))
