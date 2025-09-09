import os
import asyncio
import json
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.auth.azure import AzureTokenProvider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

load_dotenv()

class TopicGenerationSystem:
    """Multi-agent system for generating and refining concepts/topics for a tech stack"""

    def __init__(self, model_client):
        self.model_client = model_client
        self.concept_agent = self._create_concept_agent()
        self.refinement_agent = self._create_refinement_agent()

    def _create_concept_agent(self):
        """Creates the Concept Generation Agent"""
        system_message = """
        You are an expert Technical Curriculum Designer with 15+ years of experience.
        Your role is to generate a comprehensive list of key concepts for a given tech stack.
        For each concept, assign a difficulty level: beginner, intermediate, or advanced.
        Output ONLY a valid JSON array in the following format:
        [
            {"name": "Component Lifecycle", "level": "intermediate"},
            {"name": "State Management", "level": "beginner"},
            ...
        ]
        Do not include explanations, markdown, or extra text. End your response with "TERMINATE".
        """
        return AssistantAgent(
            name="concept_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )

    def _create_refinement_agent(self):
        """Creates the Concept Refinement Agent"""
        system_message = """
        You are an expert Technical Curriculum Editor.
        Your role is to refine and improve a list of concepts for a tech stack based on feedback.
        - Address specific feedback or requests for improvement.
        - Add, remove, or adjust concepts and levels as needed.
        Output ONLY a valid JSON array in the same format as received.
        End your response with "TERMINATE".
        """
        return AssistantAgent(
            name="refinement_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )

    async def generate_concepts(self, tech_stack: str) -> List[Dict[str, Any]]:
        """Generate initial concepts for the tech stack"""
        print(f"Generating concepts for tech stack: {tech_stack}")
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.concept_agent], termination_condition=termination)
        task = f"""
        Generate a list of key concepts for the following tech stack:
        {tech_stack}
        For each concept, assign a level: beginner, intermediate, or advanced.
        Output ONLY the JSON array as specified.
        """
        result = await team.run(task=task)
        concepts_json = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "concept_agent":
                content = message.content
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                concepts_json += content
        try:
            concepts = json.loads(concepts_json)
            return concepts
        except Exception as e:
            print(f"Error parsing concepts: {e}")
            return []

    async def human_concept_review(self, concepts) -> str:
        """Human-in-the-loop review and approval for concepts"""
        print("\nPlease review the generated concepts:")
        print(json.dumps(concepts, indent=2))
        print("\nOptions:")
        print("1. APPROVE - Concepts are ready")
        print("2. REFINE - Need improvements")
        print("3. FEEDBACK - Provide specific feedback")
        print("4. REJECT - Start over")
        while True:
            choice = input("\nYour choice (1-4 or word): ").strip().lower()
            if choice in ["1", "approve"]:
                return "APPROVE"
            elif choice in ["2", "refine"]:
                return "REFINE"
            elif choice in ["3", "feedback"]:
                feedback = input("Please provide specific feedback: ").strip()
                if feedback:
                    return f"FEEDBACK: {feedback}"
                else:
                    print("Please provide feedback or choose another option.")
            elif choice in ["4", "reject"]:
                return "REJECT"
            else:
                print("Invalid choice. Please try again.")

    async def refine_concepts(self, concepts: List[Dict[str, Any]], feedback: str) -> List[Dict[str, Any]]:
        """Refine concepts based on feedback using the refinement agent"""
        print("Refining concepts based on feedback...")
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.refinement_agent], termination_condition=termination)
        task = f"""
        Please refine the following list of concepts for the tech stack, based on this feedback:
        Concepts: {json.dumps(concepts, indent=2)}
        Feedback: {feedback}
        Output ONLY the JSON array as specified.
        """
        result = await team.run(task=task)
        refined_json = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "refinement_agent":
                content = message.content
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                refined_json += content
        try:
            refined_concepts = json.loads(refined_json)
            return refined_concepts
        except Exception as e:
            print(f"Error parsing refined concepts: {e}")
            return []

    async def run_topic_generation_workflow(self, tech_stack: str) -> List[Dict[str, Any]]:
        """Run the complete topic/concept generation workflow with human review"""
        concepts = await self.generate_concepts(tech_stack)
        formatted_concepts = {}
        for concept in concepts:
            if concept['level'] in formatted_concepts:
                formatted_concepts[concept['level']].append(concept['name'])
            else:
                formatted_concepts[concept['level']] = [concept['name']]
            # formatted_concepts[concept["level"]] = formatted_concepts.get(concept["level"], []).append(concept['name'])
        while True:
            decision = await self.human_concept_review(formatted_concepts)
            if decision == "APPROVE":
                print("Concepts approved.")
                return concepts
            elif decision == "REJECT":
                print("Restarting concept generation...")
                concepts = await self.generate_concepts(tech_stack)
            elif decision.startswith("FEEDBACK:"):
                feedback = decision.replace("FEEDBACK:", "").strip()
                concepts = await self.refine_concepts(concepts, feedback)
            elif decision == "REFINE":
                concepts = await self.refine_concepts(concepts, "Please improve the concept list.")


async def generate_topics(tech_stack: str) -> List[Dict[str, Any]]:
    """Generate the topics based on a tech-stack"""
    print("Generating topics...")
    try:
        model_client = AzureOpenAIChatCompletionClient(model='gpt-4.1')
        topic_gen = TopicGenerationSystem(model_client=model_client)
        topics = await topic_gen.run_topic_generation_workflow(tech_stack)
        return topics
    except Exception as e:
        print(f"Error generating topics: {e}")

if __name__ == "__main__":
    res = asyncio.run(generate_topics(input("Tech stack: ")))
    import pprint
    pprint.pprint(res)