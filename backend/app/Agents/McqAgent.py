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

class QuizGenerationSystem:
    """Multi-agent system for generating and refining quizzes based on tech stack and concepts"""
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.quiz_agent = self._create_quiz_agent()
        self.feedback_agent = self._create_feedback_agent()
        self.refinement_agent = self._create_refinement_agent()
        self.current_quiz = None
        self.feedback_history = []
        self.target_question_count = None
    
    def _create_quiz_agent(self):
        """Creates the Quiz Generation Agent"""
        system_message = """
        You are an expert Technical Quiz Creator with 15+ years of experience in educational content development.
        Your role is to create comprehensive, challenging, and accurate technical quizzes based on provided parameters.
        
        When given quiz parameters, you should:
        1. **Analyze the tech stack** and specific concepts to be tested
        2. **Create appropriate questions** that test understanding, not just memorization
        3. **Generate plausible options** with one correct answer and three incorrect but reasonable distractors
        4. **Vary question difficulty** based on the specified experience level (beginner, intermediate, advanced)
        5. **Ensure technical accuracy** of all questions and answers
        6. **Cover all requested concepts** thoroughly
        7. **Consider time constraints** based on the quiz duration
        
        **CRITICAL OUTPUT REQUIREMENT:**
        You MUST return ONLY a valid JSON object. No explanations, no markdown formatting, no additional text.
        The JSON must be properly formatted and parseable.
        
        **Required JSON Structure:**
        {
            "question1": {
                "question": "What is the primary purpose of React's useEffect hook?",
                "options": {
                    "A": "To handle state in functional components",
                    "B": "To create side effects in functional components",
                    "C": "To replace class components entirely",
                    "D": "To optimize rendering performance"
                },
                "correctAnswer": "B",
                "explanation": "The useEffect hook is used to perform side effects in functional components, such as data fetching, subscriptions, or manually changing the DOM.",
                "topics": ["React Hooks", "Functional Components"],
                "concepts": ["useEffect", "Side Effects", "Lifecycle Methods"]
            }
        }
        
        **IMPORTANT:** 
        - Return ONLY the JSON object
        - Ensure all strings are properly escaped
        - Include EXACTLY the number of questions requested (no more, no less)
        - Each question MUST include "topics" and "concepts" fields
        - Ensure questions are appropriate for the specified duration
        - End your response with "TERMINATE" after the JSON
        
        Be thorough, technically accurate, and create questions that truly test understanding of the concepts.
        """
        
        return AssistantAgent(
            name="quiz_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
    
    def _create_feedback_agent(self):
        """Creates the Quiz Feedback Agent"""
        system_message = """
        You are an expert Technical Quiz Reviewer with deep experience in:
        - Technical accuracy assessment
        - Question quality evaluation
        - Answer option analysis
        - Quiz structure and flow
        - Educational effectiveness
        
        Your role is to review generated quizzes and provide constructive feedback.
        
        **Review Criteria:**
        1. **Technical Accuracy:**
           - Are all questions and answers technically correct?
           - Do questions reflect current best practices and standards?
           - Are explanations accurate and helpful?
        
        2. **Question Quality:**
           - Are questions clear and unambiguous?
           - Do questions test understanding rather than memorization?
           - Are distractors plausible but clearly incorrect?
        
        3. **Completeness:**
           - Are all requested concepts covered?
           - Is there appropriate variety in question types?
           - Is the difficulty appropriate for the target audience?
        
        4. **Educational Value:**
           - Do questions promote learning?
           - Are explanations educational?
           - Will quiz takers learn from the experience?
        
        **Feedback Format:**
        Provide structured feedback with:
        - Overall assessment (score 1-10)
        - Strengths identified
        - Areas for improvement
        - Specific recommendations
        - Technical corrections needed
        - Question quality adjustments
        
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
        """Creates the Quiz Refinement Agent"""
        system_message = """
        You are an expert Technical Quiz Editor specializing in quiz refinement and improvement.
        Your role is to take feedback and improve the technical quiz questions.
        
        **Refinement Process:**
        1. **Analyze feedback** carefully and understand the concerns
        2. **Identify patterns** in the feedback
        3. **Prioritize improvements** based on impact
        4. **Refine questions** to address feedback points
        5. **Correct technical inaccuracies** identified in feedback
        6. **Improve answer options** for clarity and effectiveness
        7. **Enhance explanations** for educational value
        
        **Improvement Focus:**
        - Technical accuracy of questions and answers
        - Question clarity and precision
        - Distractor quality and plausibility
        - Explanation completeness and educational value
        - Concept coverage and balance
        - Difficulty calibration
        
        **CRITICAL OUTPUT REQUIREMENT:**
        You MUST return ONLY a valid JSON object. No explanations, no markdown formatting, no additional text.
        The JSON must be properly formatted and parseable.
        
        **CRITICAL CONSTRAINTS:**
        - Maintain EXACTLY the same number of questions as the original quiz
        - Each question MUST include "topics" and "concepts" fields
        - Keep the same JSON structure while improving content quality
        - Be thorough in addressing feedback and ensure the refined version is significantly better
        - End your response with "TERMINATE"
        """
        
        return AssistantAgent(
            name="refinement_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
    
    def _validate_quiz_structure(self, quiz_json: str, expected_count: int) -> tuple[bool, str]:
        """Validate quiz structure and question count"""
        try:
            quiz_data = json.loads(quiz_json)
            
            
            if not isinstance(quiz_data, dict):
                return False, "Quiz must be a JSON object"
            
            
            question_keys = [key for key in quiz_data.keys() if key.startswith('question')]
            actual_count = len(question_keys)
            
            if actual_count != expected_count:
                return False, f"Expected {expected_count} questions, but got {actual_count}"
            
            
            for i, question_key in enumerate(question_keys, 1):
                question = quiz_data[question_key]
                required_fields = ['question', 'options', 'correctAnswer', 'explanation', 'topics', 'concepts']
                
                for field in required_fields:
                    if field not in question:
                        return False, f"Question {i} missing required field: {field}"
                
                
                if not isinstance(question['options'], dict) or len(question['options']) != 4:
                    return False, f"Question {i} must have exactly 4 options (A, B, C, D)"
                
                
                if question['correctAnswer'] not in ['A', 'B', 'C', 'D']:
                    return False, f"Question {i} correctAnswer must be A, B, C, or D"
                
                
                if not isinstance(question['topics'], list) or not isinstance(question['concepts'], list):
                    return False, f"Question {i} topics and concepts must be arrays"
            
            return True, "Valid quiz structure"
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _enforce_question_count(self, quiz_json: str, target_count: int) -> str:
        """Enforce exact question count by trimming or regenerating if needed"""
        try:
            quiz_data = json.loads(quiz_json)
            question_keys = [key for key in quiz_data.keys() if key.startswith('question')]
            
            if len(question_keys) == target_count:
                return quiz_json
            
            if len(question_keys) > target_count:
                
                excess_keys = question_keys[target_count:]
                for key in excess_keys:
                    del quiz_data[key]
                print(f"Removed {len(excess_keys)} excess questions to match target count of {target_count}")
                return json.dumps(quiz_data, indent=2)
            
            
            return None
            
        except Exception as e:
            print(f"Error enforcing question count: {e}")
            return None
    
    async def generate_initial_quiz(self, quiz_params: str) -> str:
        """Generate initial quiz using team approach"""
        print("Quiz Agent: Generating initial quiz questions...")
        print("=" * 60)
        
        
        import re
        num_match = re.search(r'Number of Questions:\s*(\d+)', quiz_params)
        if num_match:
            self.target_question_count = int(num_match.group(1))
        else:
            self.target_question_count = 5  
        
        
        termination = TextMentionTermination("TERMINATE")
        
        
        team = RoundRobinGroupChat([self.quiz_agent], termination_condition=termination)
        
        task = f"""
        Generate a technical quiz based on these parameters:
        
        {quiz_params}
        
        Please create a comprehensive quiz in the specified JSON format.
        Ensure questions are technically accurate and appropriate for the specified duration.
        CRITICAL: Generate EXACTLY {self.target_question_count} questions, no more, no less.
        """
        
        
        result = await team.run(task=task)
        
        
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "quiz_agent":
                content = message.content
                
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        
        
        is_valid, validation_msg = self._validate_quiz_structure(json_content, self.target_question_count)
        if not is_valid:
            print(f"Validation failed: {validation_msg}")
            
            enforced_content = self._enforce_question_count(json_content, self.target_question_count)
            if enforced_content:
                json_content = enforced_content
                print("Question count enforced successfully")
            else:
                print("Failed to enforce question count, regenerating...")
                
                task = f"""
                Generate EXACTLY {self.target_question_count} technical quiz questions based on these parameters:
                
                {quiz_params}
                
                You MUST generate exactly {self.target_question_count} questions. Count them carefully.
                Each question must include: question, options (A,B,C,D), correctAnswer, explanation, topics, concepts.
                """
                
                result = await team.run(task=task)
                json_content = ""
                for message in result.messages:
                    if isinstance(message, TextMessage) and message.source == "quiz_agent":
                        content = message.content
                        if "TERMINATE" in content:
                            content = content.replace("TERMINATE", "").strip()
                        if content.startswith("```json") and content.endswith("```"):
                            content = content[7:-3].strip()
                        elif content.startswith("```") and content.endswith("```"):
                            content = content[3:-3].strip()
                        json_content += content
        
        print("Generated Quiz:")
        print(json_content)
        self.current_quiz = json_content
        return json_content
    
    async def get_feedback(self, quiz: str) -> str:
        """Get feedback on generated quiz using team approach"""
        print("\nFeedback Agent: Reviewing quiz questions...")
        print("=" * 60)
        
        
        termination = TextMentionTermination("TERMINATE")
        
        
        team = RoundRobinGroupChat([self.feedback_agent], termination_condition=termination)
        
        task = f"""
        Please review this generated technical quiz:
        
        {quiz}
        
        Provide comprehensive feedback on:
        - Technical accuracy of questions and answers
        - Question quality and clarity
        - Answer option quality
        - Explanation quality
        - Overall educational value
        
        Be specific and actionable in your recommendations.
        """
        
        
        result = await team.run(task=task)
        
        
        feedback_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "feedback_agent":
                content = message.content
                
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                feedback_content += content
        
        print("Feedback:")
        print(feedback_content)
        self.feedback_history.append(feedback_content)
        return feedback_content
    
    async def refine_quiz(self, quiz: str, feedback: str) -> str:
        """Refine quiz based on feedback using team approach"""
        print("\nRefinement Agent: Improving quiz based on feedback...")
        print("=" * 60)
        
        
        termination = TextMentionTermination("TERMINATE")
        
        
        team = RoundRobinGroupChat([self.refinement_agent], termination_condition=termination)
        
        task = f"""
        Please refine this technical quiz based on the feedback:
        
        **Original Quiz:**
        {quiz}
        
        **Feedback Received:**
        {feedback}
        
        **CRITICAL REQUIREMENTS:**
        - Maintain EXACTLY {self.target_question_count} questions (no more, no less)
        - Each question must include: question, options (A,B,C,D), correctAnswer, explanation, topics, concepts
        - Improve the quiz by addressing the feedback points
        - Maintain the JSON structure while significantly improving content quality
        """
        
        
        result = await team.run(task=task)
        
        
        refined_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "refinement_agent":
                content = message.content
                
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                refined_content += content
        
        
        is_valid, validation_msg = self._validate_quiz_structure(refined_content, self.target_question_count)
        if not is_valid:
            print(f"Refinement validation failed: {validation_msg}")
            
            enforced_content = self._enforce_question_count(refined_content, self.target_question_count)
            if enforced_content:
                refined_content = enforced_content
                print("Question count enforced after refinement")
            else:
                print("Warning: Could not enforce question count after refinement")
        
        print("Refined Quiz:")
        print(refined_content)
        self.current_quiz = refined_content
        return refined_content
    
    async def human_review(self, quiz: str) -> str:
        """Human-in-the-loop review and approval using UserProxyAgent"""
        print("\nHuman Review: Please review the final quiz...")
        print("=" * 60)
        print("Generated Quiz:")
        print(quiz)
        print("\n" + "=" * 60)
        
        
        def user_input_func(prompt: str, cancellation_token: CancellationToken | None = None) -> str:
            print(f"\n{prompt}")
            print("\nOptions:")
            print("1. APPROVE - Quiz is ready")
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
        
        
        user_proxy = UserProxyAgent("user_proxy", input_func=user_input_func)
        
        
        approve_termination = TextMentionTermination("APPROVE")
        refine_termination = TextMentionTermination("REFINE")
        feedback_termination = TextMentionTermination("FEEDBACK:")
        reject_termination = TextMentionTermination("REJECT")
        
        
        termination = approve_termination | refine_termination | feedback_termination | reject_termination
        
        
        team = RoundRobinGroupChat([user_proxy], termination_condition=termination)
        
        
        result = await team.run(task="Please review the quiz and provide your decision.")
        
        
        user_decision = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "user_proxy":
                user_decision = message.content
                break
        
        return user_decision
    
    async def run_complete_workflow(self, quiz_params: str):
        """Run the complete quiz generation workflow"""
        print("Starting Quiz Generation Workflow")
        print("=" * 60)
        
        
        quiz = await self.generate_initial_quiz(quiz_params)
        
        
        feedback = await self.get_feedback(quiz)
        
        
        refined_quiz = await self.refine_quiz(quiz, feedback)
        
        
        while True:
            human_decision = await self.human_review(refined_quiz)
            
            if human_decision == "APPROVE":
                print("\nQuiz generation completed successfully!")
                
                try:
                    json_obj = json.loads(refined_quiz)
                    return json_obj
                except json.JSONDecodeError:
                    print("Warning: Final quiz is not valid JSON. Returning as string.")
                    return refined_quiz
            elif human_decision == "REJECT":
                print("\nStarting over with new approach...")
                quiz = await self.generate_initial_quiz(quiz_params)
                feedback = await self.get_feedback(quiz)
                refined_quiz = await self.refine_quiz(quiz, feedback)
            elif human_decision.startswith("FEEDBACK:"):
                specific_feedback = human_decision.replace("FEEDBACK: ", "")
                print(f"\nRefining based on your feedback: {specific_feedback}")
                refined_quiz = await self.refine_quiz(refined_quiz, specific_feedback)
            elif human_decision == "REFINE":
                print("\nRequesting additional refinement...")
                additional_feedback = await self.get_feedback(refined_quiz)
                refined_quiz = await self.refine_quiz(refined_quiz, additional_feedback)

async def generate_quiz(tech_stack: str, concepts: str, num_questions: str, duration: str, experience_level: str = "intermediate"):
    """Function to generate a quiz with the specified parameters and return JSON"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "<your_openai_api_key_here>":
        print("Please set your OpenAI API key in the .env file")
        return None

    
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"), 
    )



    
    quiz_system = QuizGenerationSystem(model_client)
    
    
    quiz_params = f"""
    Tech Stack: {tech_stack}
    Concepts: {concepts}
    Number of Questions: {num_questions}
    Duration: {duration} minutes
    Experience Level: {experience_level}
    """

    try:
        
        final_quiz = await quiz_system.run_complete_workflow(quiz_params)
        return final_quiz
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        await model_client.close()

async def main():
    """Main function to run the quiz generation system"""
    print("Technical Quiz Generation System")
    print("=" * 60)
    print("This system will:")
    print("1. Generate comprehensive technical quiz questions")
    print("2. Review and provide feedback")
    print("3. Refine based on feedback")
    print("4. Include human review and approval")
    print("=" * 60)

    
    print("\nPlease provide quiz parameters:")
    tech_stack = input("Tech Stack (e.g., 'React, Node.js, MongoDB'): ").strip()
    concepts = input("Specific Concepts to Test (e.g., 'Hooks, State Management, Routing'): ").strip()
    num_questions = input("Number of Questions: ").strip()
    duration = input("Quiz Duration (in minutes): ").strip()
    experience_level = input("Experience Level (beginner, intermediate, advanced): ").strip() or "intermediate"
    
    
    quiz_params = f"""
    Tech Stack: {tech_stack}
    Concepts: {concepts}
    Number of Questions: {num_questions}
    Duration: {duration} minutes
    Experience Level: {experience_level}
    """

    try:
        
        final_quiz = await generate_quiz(tech_stack, concepts, num_questions, duration, experience_level)
        
        print("\nFinal Quiz:")
        print("=" * 60)
        print(json.dumps(final_quiz, indent=2))
        
        
        save_to_file = input("\nDo you want to save the quiz to a file? (y/n): ").strip().lower()
        if save_to_file == 'y':
            filename = input("Enter filename (default: quiz.json): ").strip() or "quiz.json"
            if not filename.endswith(".json"):
                filename += ".json"
            with open(filename, 'w') as f:
                json.dump(final_quiz, f, indent=2)
            print(f"Quiz saved to {filename}")
        
    except Exception as e:
        print(f"Error: {e}")

