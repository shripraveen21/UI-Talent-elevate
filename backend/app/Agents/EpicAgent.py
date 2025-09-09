import os
import asyncio
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import UserMessage
from autogen_ext.auth.azure import AzureTokenProvider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage
from autogen_agentchat.ui import Console
# from azure.identity import DefaultAzureCredentia  
 
load_dotenv()

class EpicGenerationSystem:
    """Multi-agent system for generating and refining epics and user stories"""
   
    def __init__(self, model_client):
        self.model_client = model_client
        self.epic_agent = self._create_epic_agent()
        self.feedback_agent = self._create_feedback_agent()
        self.refinement_agent = self._create_refinement_agent()
        self.current_epics = None
        self.feedback_history = []
   
    def _create_epic_agent(self):
        """Creates the Epic Generation Agent"""
        system_message = """
        You are an expert Product Owner and Agile Coach with 15+ years of experience.
        Your role is to analyze POC ideas and generate comprehensive, well-structured Epics and User Stories.
       
        When given a POC idea, you should:
        1. **Analyze the business value** and user needs
        2. **Identify all user personas** (end users, admins, stakeholders)
        3. **Break down into logical epics** that represent major feature areas
        4. **Generate detailed user stories** for each epic
        5. **Consider technical dependencies** and implementation order
        6. **Include acceptance criteria** for each user story
        7. **Think about edge cases** and error scenarios
       
        **CRITICAL OUTPUT REQUIREMENT:**
        You MUST return ONLY a valid JSON object. No explanations, no markdown formatting, no additional text.
        The JSON must be properly formatted and parseable.
       
        **Required JSON Structure:**
        {
            "Epic1": {
                "title": "User Authentication & Management",
                "description": "Complete user authentication and profile management system",
                "userStories": [
                    {
                        "title": "User Registration",
                        "description": "As a new user, I want to create an account so that I can access the platform",
                        "acceptanceCriteria": [
                            "User can register with email and password",
                            "Email verification is required",
                            "Password meets security requirements"
                        ],
                        "priority": "High",
                        "effort": "Medium"
                    }
                ]
            }
        }
       
        **IMPORTANT:**
        - Return ONLY the JSON object
        - Ensure all strings are properly escaped
        - Include 5-8 comprehensive epics
        - Each epic should have 3-6 user stories
        - End your response with "TERMINATE" after the JSON
       
        Be thorough, think about all possible scenarios, and ensure user stories are actionable and testable.
        """
       
        return AssistantAgent(
            name="epic_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
   
    def _create_feedback_agent(self):
        """Creates the Story Feedback Agent"""
        system_message = """
        You are an expert Agile Coach and User Story reviewer with deep experience in:
        - User story quality assessment
        - Acceptance criteria validation
        - Epic organization and prioritization
        - Technical feasibility analysis
        - Business value alignment
       
        Your role is to review generated epics and user stories and provide constructive feedback.
       
        **Review Criteria:**
        1. **User Story Quality:**
           - Are stories written from user perspective?
           - Do they follow "As a [user], I want [goal] so that [benefit]" format?
           - Are acceptance criteria clear and testable?
           - Are stories appropriately sized (not too large/small)?
       
        2. **Epic Organization:**
           - Are epics logically grouped?
           - Is there clear separation of concerns?
           - Are dependencies properly identified?
       
        3. **Completeness:**
           - Are all major features covered?
           - Are edge cases and error scenarios considered?
           - Are technical and non-functional requirements included?
       
        4. **Business Value:**
           - Do stories align with business objectives?
           - Is prioritization logical?
           - Are user personas properly considered?
       
        **Feedback Format:**
        Provide structured feedback with:
        - Overall assessment (score 1-10)
        - Strengths identified
        - Areas for improvement
        - Specific recommendations
        - Missing elements
        - Priority adjustments
       
        Be constructive, specific, and actionable in your feedback.
        End your response with "TERMINATE".
        """
       
        return AssistantAgent(
            name="feedback_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
   
    def _create_refinement_agent(self):
        """Creates the Story Refinement Agent"""
        system_message = """
        You are an expert Product Owner specializing in story refinement and iteration.
        Your role is to take feedback and improve the epics and user stories.
       
        **Refinement Process:**
        1. **Analyze feedback** carefully and understand the concerns
        2. **Identify patterns** in the feedback
        3. **Prioritize improvements** based on impact and effort
        4. **Refine user stories** to address feedback points
        5. **Reorganize epics** if needed for better structure
        6. **Add missing elements** identified in feedback
        7. **Improve acceptance criteria** for clarity and testability
       
        **Improvement Focus:**
        - Better user story structure and clarity
        - More comprehensive acceptance criteria
        - Logical epic organization
        - Proper prioritization
        - Technical feasibility
        - Business value alignment
       
        **CRITICAL OUTPUT REQUIREMENT:**
        You MUST return ONLY a valid JSON object. No explanations, no markdown formatting, no additional text.
        The JSON must be properly formatted and parseable.
       
        Always maintain the same JSON structure while improving content quality.
        Be thorough in addressing feedback and ensure the refined version is significantly better.
        End your response with "TERMINATE".
        """
       
        return AssistantAgent(
            name="refinement_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
   
    async def   generate_initial_epics(self, poc_details: str) -> str:
        """Generate initial epics and user stories using team approach"""
        print("Epic Agent: Generating initial epics and user stories...")
        print("=" * 60)
       
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
       
        # Create team with epic agent
        team = RoundRobinGroupChat([self.epic_agent], termination_condition=termination)
       
        task = f"""
        Analyze this POC idea and generate comprehensive epics and user stories:
       
        {poc_details}
       
        Please provide a detailed analysis and generate epics with user stories in the specified JSON format.
        Consider all user personas, technical requirements, and business scenarios.
        """
       
        # Run the team and collect result
        result = await team.run(task=task)
       
        # Extract the JSON content from the result
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "epic_agent":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                json_content += content
       
        print("Generated Epics:")
        print(json_content)
        self.current_epics = json_content
        return json_content
   
    async def get_feedback(self, epics: str) -> str:
        """Get feedback on generated epics using team approach"""
        print("\nFeedback Agent: Reviewing epics and user stories...")
        print("=" * 60)
       
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
       
        # Create team with feedback agent
        team = RoundRobinGroupChat([self.feedback_agent], termination_condition=termination)
       
        task = f"""
        Please review these generated epics and user stories:
       
        {epics}
       
        Provide comprehensive feedback on:
        - User story quality and structure
        - Epic organization and completeness
        - Business value alignment
        - Technical feasibility
        - Areas for improvement
       
        Be specific and actionable in your recommendations.
        """
       
        # Run the team and collect result
        result = await team.run(task=task)
       
        # Extract the feedback content from the result
        feedback_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "feedback_agent":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                feedback_content += content
       
        print("Feedback:")
        print(feedback_content)
        self.feedback_history.append(feedback_content)
        return feedback_content
   
    async def refine_epics(self, epics: str, feedback: str) -> str:
        """Refine epics based on feedback using team approach"""
        print("\nRefinement Agent: Improving epics based on feedback...")
        print("=" * 60)
       
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
       
        # Create team with refinement agent
        team = RoundRobinGroupChat([self.refinement_agent], termination_condition=termination)
       
        task = f"""
        Please refine these epics and user stories based on the feedback:
       
        **Original Epics:**
        {epics}
       
        **Feedback Received:**
        {feedback}
       
        Improve the epics and user stories by addressing the feedback points.
        Maintain the JSON structure while significantly improving content quality.
        """
       
        # Run the team and collect result
        result = await team.run(task=task)
       
        # Extract the refined content from the result
        refined_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "refinement_agent":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                refined_content += content
       
        print("Refined Epics:")
        print(refined_content)
        self.current_epics = refined_content
        return refined_content
   
    async def human_review(self, epics: str) -> str:
        """Human-in-the-loop review and approval using UserProxyAgent"""
        print("\nHuman Review: Please review the final epics...")
        print("=" * 60)
        print("Generated Epics and User Stories:")
        print(epics)
        print("\n" + "=" * 60)
       
        # Create a simple input function for user interaction
        def user_input_func(prompt: str, cancellation_token: CancellationToken | None = None) -> str:
            print(f"\n{prompt}")
            print("\nOptions:")
            print("1. APPROVE - Epics are ready")
            print("2. REFINE - Need improvements")
            print("3. FEEDBACK - Provide specific feedback")
            print("4. REJECT - Start over")
           
            while True:
                choice = input("\nYour choice (1-4): ").strip()
               
                if choice == "1":
                    return "APPROVE"
                elif choice == "2":
                    return "REFINE"
                elif choice == "3":
                    feedback = input("Please provide specific feedback: ").strip()
                    if feedback:
                        return f"FEEDBACK: {feedback}"
                    else:
                        print("Please provide feedback or choose another option.")
                elif choice == "4":
                    return "REJECT"
                else:
                    print("Invalid choice. Please try again.")
       
        # Create UserProxyAgent
        user_proxy = UserProxyAgent("user_proxy", input_func=user_input_func)
       
        # Create termination conditions
        approve_termination = TextMentionTermination("APPROVE")
        refine_termination = TextMentionTermination("REFINE")
        feedback_termination = TextMentionTermination("FEEDBACK:")
        reject_termination = TextMentionTermination("REJECT")
       
        # Combine termination conditions
        termination = approve_termination | refine_termination | feedback_termination | reject_termination
       
        # Create team with user proxy
        team = RoundRobinGroupChat([user_proxy], termination_condition=termination)
       
        # Run the team
        result = await team.run(task="Please review the epics and provide your decision.")
       
        # Extract user decision
        user_decision = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "user_proxy":
                user_decision = message.content
                break
       
        return user_decision
   
    async def run_complete_workflow(self, poc_details: str):
        """Run the complete epic generation workflow"""
        print("Starting Epic Generation Workflow")
        print("=" * 60)
       
        # Step 1: Generate initial epics
        epics = await self.generate_initial_epics(poc_details)
       
        # Step 2: Get feedback
        feedback = await self.get_feedback(epics)
       
        # Step 3: Refine based on feedback
        refined_epics = await self.refine_epics(epics, feedback)
       
        # Step 4: Human review loop
        max_iterations = 3
        iteration = 0
       
        while iteration < max_iterations:
            human_decision = await self.human_review(refined_epics)
           
            if human_decision == "APPROVE":
                print("\nEpic generation completed successfully!")
                return refined_epics
            elif human_decision == "REJECT":
                print("\nStarting over with new approach...")
                epics = await self.generate_initial_epics(poc_details)
                feedback = await self.get_feedback(epics)
                refined_epics = await self.refine_epics(epics, feedback)
                iteration = 0
            elif human_decision.startswith("FEEDBACK:"):
                specific_feedback = human_decision.replace("FEEDBACK: ", "")
                print(f"\nRefining based on your feedback: {specific_feedback}")
                refined_epics = await self.refine_epics(refined_epics, specific_feedback)
            elif human_decision == "REFINE":
                print("\nRequesting additional refinement...")
                additional_feedback = await self.get_feedback(refined_epics)
                refined_epics = await self.refine_epics(refined_epics, additional_feedback)
           
            iteration += 1
       
        if iteration >= max_iterations:
            print("\nMaximum iterations reached. Using current version.")
       
        return refined_epics
 
async def main():
    """Main function to run the epic generation system"""
    # openai_key = os.getenv("OPENAI_API_KEY")
    # if not openai_key or openai_key == "<your_openai_api_key_here>":
    #     print("Please set your OpenAI API key in the .env file")
    #     return
    
    # Define the model client
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        # azure_endpoint = AZURE_OPENAI_ENDPOINT,
        # api_key = AZURE_OPENAI_API_KEY
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"), # For key-based authentication.
    )

    print("key",os.getenv("AZURE_OPENAI_API_KEY"))
    print("key we F",os.getenv("AZURE_OPENAI_ENDPOINT"))
    
 
    # Create the epic generation system
    epic_system = EpicGenerationSystem(model_client)
 
    print("Epic & User Story Generation System")
    print("=" * 60)
    print("This system will:")
    print("1. Generate comprehensive epics and user stories")
    print("2. Review and provide feedback")
    print("3. Refine based on feedback")
    print("4. Include human review and approval")
    print("=" * 60)
 
    # Default POC data for development
    print("\nUsing default POC data for development...")
    poc_details = """
    POC Title: Smart E-commerce Platform with AI Recommendations
    Description: A modern e-commerce platform that uses AI to provide personalized product recommendations, dynamic pricing, and intelligent inventory management. The platform will serve both B2C and B2B customers with different user experiences.
    Features: AI product recommendations, dynamic pricing engine, inventory management, multi-vendor marketplace, mobile app, analytics dashboard, payment integration, order tracking, customer reviews, wishlist functionality
    Tech Stack: React.js, Node.js, Express, MongoDB, Redis, TensorFlow, Stripe API, AWS S3, Docker, Kubernetes
    Target Users: Online shoppers, store owners, marketplace vendors, platform administrators, marketing team, customer support
    Business Goals: Increase sales conversion by 25%, reduce cart abandonment by 30%, improve customer satisfaction scores, expand to new markets, reduce operational costs by 20%
    """
 
    try:
        # Run the complete workflow
        final_epics = await epic_system.run_complete_workflow(poc_details)
       
        print("\nFinal Epics and User Stories:")
        print("=" * 60)
        print(final_epics)
       
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await model_client.close()
 
if __name__ == "__main__":
    asyncio.run(main())