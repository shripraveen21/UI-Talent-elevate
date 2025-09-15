import asyncio
import json
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from typing import Dict
import os
from pathlib import Path
load_dotenv()

class QuizFeedbackAnalyzer:
    """
    Agent-based workflow for analyzing quiz results and generating structured feedback, now with a Critic Agent.
    """

    def __init__(self, model_client):
        self.model_client = model_client

        self.parser_agent = AssistantAgent(
            name="QuizParser",
            model_client=self.model_client,
            system_message=self._get_parser_system_message(),
        )
        self.topic_agent = AssistantAgent(
            name="TopicExtractor",
            model_client=self.model_client,
            system_message=self._get_topic_system_message(),
        )
        self.analysis_agent = AssistantAgent(
            name="PerformanceAnalyzer",
            model_client=self.model_client,
            system_message=self._get_analysis_system_message(),
        )
        self.feedback_agent = AssistantAgent(
            name="FeedbackGenerator",
            model_client=self.model_client,
            system_message=self._get_feedback_system_message(),
        )
        self.resource_agent = AssistantAgent(
            name="LearningResourceAgent",
            model_client=self.model_client,
            system_message=self._get_resource_system_message(),
        )
        self.critic_agent = AssistantAgent(
            name="CriticAgent",
            model_client=self.model_client,
            system_message=self._get_critic_system_message(),
        )

    def _get_parser_system_message(self) -> str:
        return """You are the QuizParser agent. Your job is to read the quiz data and extract:
- Total number of question present in the quiz
- Number of correct answers
- Score percentage (rounded to nearest integer)
Output ONLY the following JSON:
{
  "quiz_result": {
    "total_questions": <integer>,
    "correct_answers": <integer>,
    "score_percentage": <integer>
  }
}
Do not add any explanations or extra information."""

    def _get_topic_system_message(self) -> str:
        return """You are the TopicExtractor agent. Analyze the quiz and identify main topics (tech stacks) and subtopics (concepts) covered.
Output ONLY the following JSON:
{
  "topics": [
    {
      "topic": "<topic_name>",
      "concepts": ["<concept_1>", "<concept_2>", ...]
    }
  ]
}
Do not add explanations or unrelated information."""

    def _get_analysis_system_message(self) -> str:
        return """You are the PerformanceAnalyzer agent. For each topic, calculate the number of correct and incorrect answers, and determine if the topic is a strength or weakness.

    Output ONLY the following JSON:

    {
      "analysis": [
        {
          "topic": "<topic_name>",
          "score": { "correct": <integer>, "incorrect": <integer> },
          "status": "<strength|weakness>",
          "concepts_mastered": ["<concept_1>", ...],
          "concepts_weak": ["<concept_1>", ...]
        }
      ]
    }

    Do not add explanations or extra information."""

    def _get_feedback_system_message(self) -> str:
        return """You are the FeedbackGenerator agent. For each topic, provide detailed feedback in the following JSON structure:

    {
      "analysis": [
        {
          "topic": "<topic_name>",
          "score": { "correct": <integer>, "incorrect": <integer> },
          "status": "<strength|weakness>",
          "concepts_mastered": ["<concept_1>", ...],
          "concepts_weak": ["<concept_1>", ...],
          "remarks": "<brief remark>",
          "areas_of_improvement": "<specific improvement suggestion, only if status is weakness>"
        }
      ]
    }

    Instructions:
    - For each topic, fill in the correct/incorrect counts, status ("strength" if mostly correct, "weakness" if mostly incorrect).
    - List mastered and weak concepts for each topic.
    - Add a concise remark for each topic.
    - For weaknesses, provide a specific area of improvement.
    - Do not add explanations or unrelated information. Output ONLY the JSON."""

    def _get_resource_system_message(self) -> str:
        return """You are the LearningResourceAgent. 
        For each weakness (topic and concepts_weak), suggest a relevant, high-quality online learning resource (URL) that addresses the topic or concept. 
        Output ONLY the following JSON:
      {
        "resources": [
            {
              "topic": "<topic_name>",
              "resource_url": "<url>"
            }
        ]
      }
    Do not add explanations or unrelated information."""

    def _get_critic_system_message(self) -> str:
        return """You are the CriticAgent. 
        Review the feedback JSON generated by the team for:

    - Completeness and clarity
    - Actionability of remarks and improvement suggestions
    - Adherence to required JSON format
    - Relevance and quality of suggested learning resources (resource URLs)
    - Whether each weakness has a matching resource
    Provide your critique as a valid JSON object:
    {
      "critique": {
        "overall_score": <integer 1-10>,
        "strengths": [<list of strengths>],
        "weaknesses": [<list of weaknesses>],
        "recommendations": [<list of actionable suggestions>]
      }
    }
    Do not add explanations or extra text. Only output the JSON object."""

    async def analyze_quiz(self, quiz_data: str) -> Dict[str, str]:
        """
        Analyze quiz data and generate structured feedback using multi-agent collaboration, including a Critic Agent.
        Returns:
            Dictionary containing 'feedback_json', 'critique_json', 'full_conversation'
        """
        initial_task = f"""
        Team Task: Analyze the following quiz data and generate structured feedback.
        QUIZ DATA:
        {quiz_data}
        WORKFLOW:
        1. QuizParser: Extract quiz results (total questions, correct answers, score percentage)
        2. TopicExtractor: Identify topics and concepts covered
        3. PerformanceAnalyzer: Assess strengths and weaknesses per topic/concept
        4. FeedbackGenerator: Add remarks and improvement suggestions
        5. LearningResourceAgent: For each weakness, suggest a relevant, high-quality online learning resource (URL) for further study
        Each agent should build upon the previous agent's work, staying strictly within their domain expertise.
        QuizParser: Start by providing your structured analysis.
        """

        team = RoundRobinGroupChat(
            participants=[self.parser_agent, self.topic_agent, self.analysis_agent, self.feedback_agent, self.resource_agent],
            termination_condition=MaxMessageTermination(8)
        )

        task_message = TextMessage(content=initial_task, source="user")
        result = await team.run(task=task_message)
        messages = result.messages

        # --- Aggregate outputs from agents ---
        quiz_result = None
        analysis = None
        resources = None

        for message in messages:
            if hasattr(message, 'source'):
                if message.source == "QuizParser":
                    try:
                        quiz_result = json.loads(message.content)["quiz_result"]
                    except Exception:
                        pass
                if message.source == "FeedbackGenerator":
                    try:
                        analysis = json.loads(message.content)["analysis"]
                    except Exception:
                        pass
                if message.source == "LearningResourceAgent":
                    try:
                        resources = json.loads(message.content)["resources"]
                    except Exception:
                        pass

        # Fallbacks if parsing fails
        if not quiz_result:
            for message in messages:
                if hasattr(message, 'source') and message.source == "QuizParser":
                    try:
                        quiz_result = json.loads(message.content)
                    except Exception:
                        quiz_result = message.content
        if not analysis:
            for message in messages:
                if hasattr(message, 'source') and message.source == "FeedbackGenerator":
                    try:
                        analysis = json.loads(message.content)
                    except Exception:
                        analysis = message.content

        if not resources:
            for message in messages:
                if hasattr(message, 'source') and message.source == "FeedbackGenerator":
                    try:
                        resources = json.loads(message.content)
                    except Exception:
                        resources = message.content

        # Compose final feedback JSON
        feedback_dict = {
            "quiz_result": quiz_result,
            "analysis": analysis,
            "resources": resources
        }
        feedback_json = json.dumps(feedback_dict, indent=2)

        # --- Critic Agent Review ---
        critic_task = f"""
        Please review the following feedback JSON and provide a structured critique:
        {feedback_json}
        """
        critic_team = RoundRobinGroupChat(
            participants=[self.critic_agent],
            termination_condition=MaxMessageTermination(2)
        )
        critic_task_message = TextMessage(content=critic_task, source="user")
        critic_result = await critic_team.run(task=critic_task_message)

        critique_json = ""
        for message in critic_result.messages:
            if hasattr(message, 'source') and message.source == "CriticAgent":
                critique_json = message.content

        if not critique_json:
            # Fallback: last message from CriticAgent
            agent_messages = [msg for msg in critic_result.messages if hasattr(msg, 'source') and msg.source != "user"]
            if agent_messages:
                critique_json = agent_messages[-1].content

        return {
            "feedback_json": feedback_json,
            "critique_json": critique_json,
            "full_conversation": [msg.content for msg in messages if hasattr(msg, 'content')]
        }

    async def save_feedback(self, feedback_json: str, output_dir: str = "output") -> str:
        """
            Saves the feedback JSON to the specified output directory.
            :param feedback_json: The feedback JSON to save.
            :param output_dir: The output directory.
        """
        Path(output_dir).mkdir(exist_ok=True)
        feedback_path = os.path.join(output_dir, "quiz_feedback.json")
        with open(feedback_path, 'w', encoding='utf-8') as f:
            f.write(feedback_json)
        return feedback_path


async def generate_feedback(quiz_data: str, output_dir: str = "feedback") -> str:
    model_client =AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_AZURE_OPENAI_API_KEY"), 
    )
    print("Generating feedback...")
    feedback_workflow = QuizFeedbackAnalyzer(model_client=model_client)
    analyzed_quiz = await feedback_workflow.analyze_quiz(quiz_data)
    feedback_path = await feedback_workflow.save_feedback(analyzed_quiz.get("feedback_json"), output_dir)
    print("Saved feedback successfully at: {}".format(feedback_path))
    return analyzed_quiz.get("feedback_json")


async def main() -> None:

    # user_answers = json.load(open("user_answers.json"))
    # await generate_feedback(user_answers)
    qd = json.load(open("quiz_data.json"))
    await generate_feedback(qd, 'feedback2')


if __name__ == "__main__":
    asyncio.run(main())
