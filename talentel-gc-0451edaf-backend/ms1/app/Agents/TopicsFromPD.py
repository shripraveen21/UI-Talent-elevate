import os
import asyncio
import json
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

load_dotenv()

class ProjectTechStackTopicAgent:
    """Agent that generates topics from project requirements and tech stack."""

    def __init__(self, model_client):
        self.model_client = model_client
        self.topic_agent = self._create_topic_agent()

    def _create_topic_agent(self):
        system_message = """
        You are an expert curriculum designer.
        Given a project requirements description and a tech stack, generate a JSON array of key topics/concepts that are essential for successfully delivering the project using ONLY the specified tech stack.

        - For each topic, assign a difficulty level: beginner, intermediate, or advanced.
        - ONLY include topics directly relevant to the technologies in the tech stack.
        - If the tech stack is Python, do NOT include topics about React, JavaScript, or any other technology not listed in the tech stack, even if the project description mentions them.
        - If the tech stack is React, do NOT include topics about Python, Flask, etc.
        - Exclude any topic that cannot be implemented using the provided tech stack.

        Output ONLY a valid JSON array, e.g.:
        [
            {"name": "Python File Handling", "level": "beginner"},
            {"name": "Building REST API with Flask", "level": "intermediate"}
        ]
        Do not include explanations, markdown, or extra text. End your response with "TERMINATE".
        """
        return AssistantAgent(
            name="topic_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )

    async def generate_topics(self, requirements: str, tech_stack: str):
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.topic_agent], termination_condition=termination)
        task = f"""
        Based on the following project requirements and tech stack, generate a list of key topics/concepts with difficulty levels:
        Project requirements: {requirements}
        Tech stack: {tech_stack}
        Output ONLY the JSON array as specified.
        """
        result = await team.run(task=task)
        topics_json = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "topic_agent":
                content = message.content
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                topics_json += content
        try:
            topics = json.loads(topics_json)
            return topics
        except Exception as e:
            print(f"Error parsing topics: {e}")
            return []

async def main():
    requirements = input("Enter project requirements: ")
    tech_stack = input("Enter tech stack (e.g., React, Node.js, MongoDB): ")
    model_client = AzureOpenAIChatCompletionClient(model='gpt-4.1')
    agent = ProjectTechStackTopicAgent(model_client)
    topics = await agent.generate_topics(requirements, tech_stack)
    print("\nGenerated Topics:")
    print(json.dumps(topics, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
