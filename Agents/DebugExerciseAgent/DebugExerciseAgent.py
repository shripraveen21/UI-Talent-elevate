import os
import asyncio
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from autogen_core.models import UserMessage
from autogen_ext.auth.azure import AzureTokenProvider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage, StructuredMessage
from autogen_agentchat.ui import Console
# from azure.identity import DefaultAzureCredential

load_dotenv()

class DebugExerciseGenerator:
    """Agent for generating debugging exercises based on topics, concepts, number of questions, and duration"""
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.exercise_generator = self._create_exercise_generator()
        self.difficulty_calibrator = self._create_difficulty_calibrator()
    
    def _create_exercise_generator(self):
        """Creates the Debug Exercise Generator Agent"""
        system_message = """
        You are an expert Debugging Exercise Creator with 15+ years of experience in software development and technical education.
        Your role is to create realistic, challenging, and educational debugging exercises based on specific technology topics and concepts.
        
        **Exercise Creation Guidelines:**
        1. **Technology Focus:** Create exercises that are specific to the requested technology stack
        2. **Realistic Scenarios:** Base exercises on common real-world debugging situations
        3. **Progressive Difficulty:** Structure exercises to build debugging skills progressively
        4. **Multiple Bug Types:** Include various types of bugs (logic, syntax, runtime, performance, etc.)
        5. **Clear Context:** Provide sufficient context for understanding the problem
        6. **Educational Value:** Ensure exercises teach debugging techniques and best practices
        
        **Exercise Structure Requirements:**
        - **Title:** Clear, descriptive title
        - **Description:** Detailed problem description with context
        - **Technology:** Specific tech stack and version
        - **Difficulty:** Easy, Medium, or Hard
        - **Code:** Buggy code that needs to be fixed
        - **Expected Behavior:** What the code should do
        - **Current Behavior:** What the code currently does wrong
        - **Hints:** Progressive hints (3 levels)
        - **Solution:** Complete corrected code
        - **Explanation:** Detailed explanation of the bug and fix
        - **Learning Objectives:** What skills this exercise teaches
        - **Estimated Time:** Time to solve in minutes
        
        **CRITICAL OUTPUT REQUIREMENT:**
        You MUST return ONLY a valid JSON object. No explanations, no markdown formatting, no additional text.
        The JSON must be properly formatted and parseable.
        
        **Required JSON Structure:**
        {
            "exercises": [
                {
                    "id": "exercise_1",
                    "title": "Memory Leak in React Component",
                    "description": "A React component is causing memory leaks due to improper cleanup of event listeners and timers.",
                    "technology": "React 18, JavaScript ES6+",
                    "difficulty": "Medium",
                    "code": "// Buggy code here",
                    "expectedBehavior": "Component should clean up resources on unmount",
                    "currentBehavior": "Memory usage increases with each mount/unmount cycle",
                    "hints": {
                        "level1": "Check component lifecycle methods",
                        "level2": "Look for event listeners and timers that aren't cleaned up",
                        "level3": "Use useEffect cleanup function to remove listeners and clear timers"
                    },
                    "solution": "// Corrected code here",
                    "explanation": "The bug was caused by...",
                    "learningObjectives": [
                        "Understanding React component lifecycle",
                        "Memory leak prevention techniques",
                        "Proper cleanup of side effects"
                    ],
                    "tags": ["react", "memory-leak", "useEffect", "cleanup"],
                    "estimatedTime": 15
                }
            ],
            "metadata": {
                "totalQuestions": 1,
                "totalDuration": 15,
                "difficultyDistribution": {
                    "Easy": 0,
                    "Medium": 1,
                    "Hard": 0
                },
                "topics": ["React", "Memory Management"],
                "concepts": ["Component Lifecycle", "Event Listeners", "Cleanup"]
            }
        }
        
        **IMPORTANT:** 
        - Return ONLY the JSON object
        - Ensure all strings are properly escaped
        - Include realistic, educational code examples
        - Make exercises appropriate for the specified difficulty level
        - Distribute difficulty levels based on total duration
        - End your response with "TERMINATE" after the JSON
        
        Create exercises that are challenging but solvable, with clear learning outcomes.
        """
        
        return AssistantAgent(
            name="exercise_generator",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
    
    def _create_difficulty_calibrator(self):
        """Creates the Difficulty Calibration Agent"""
        system_message = """
        You are an expert Difficulty Calibration Specialist with deep experience in:
        - Technical skill assessment
        - Learning curve analysis
        - Exercise difficulty evaluation
        - Educational progression design
        
        Your role is to calibrate debugging exercises to appropriate difficulty levels and ensure proper time distribution.
        
        **Difficulty Level Criteria:**
        
        **EASY:**
        - Single, obvious bugs (syntax errors, typos, simple logic errors)
        - Clear error messages or obvious symptoms
        - Basic debugging techniques (console.log, simple inspection)
        - 1-2 concepts to understand
        - 5-15 minutes to solve
        
        **MEDIUM:**
        - Multiple related bugs or complex single bugs
        - Requires understanding of framework/library concepts
        - Intermediate debugging techniques (debugger, network inspection, etc.)
        - 2-4 concepts to understand
        - 15-30 minutes to solve
        
        **HARD:**
        - Complex bugs involving multiple systems or components
        - Requires deep understanding of technology stack
        - Advanced debugging techniques (profiling, memory analysis, etc.)
        - 4+ concepts to understand
        - 30+ minutes to solve
        
        **Time Distribution Guidelines:**
        - Calculate appropriate difficulty distribution based on total duration
        - Ensure exercises fit within the specified time constraints
        - Balance difficulty levels to provide progressive learning
        
        **Calibration Process:**
        1. **Analyze the exercises** for complexity factors
        2. **Evaluate required knowledge** and skills
        3. **Assess debugging techniques** needed
        4. **Consider time to solve** realistically
        5. **Adjust difficulty** if needed
        6. **Provide justification** for difficulty level
        
        **Output Format:**
        Provide structured feedback with:
        - Overall difficulty assessment
        - Time distribution analysis
        - Recommended adjustments (if any)
        - Justification for difficulty levels
        - Specific suggestions for improvement
        
        **IMPORTANT:** At the end of your response, clearly state either:
        - "APPROVE" if the exercises meet all requirements
        - "REJECT" if the exercises need significant changes
        
        Be thorough and specific in your calibration analysis.
        End your response with "TERMINATE".
        """
        
        return AssistantAgent(
            name="difficulty_calibrator",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
    
    async def generate_exercises(self, topics: List[str], concepts: List[str], num_questions: int, duration_minutes: int, difficulty_level: str = "Mixed") -> Dict[str, Any]:
        """Generate debugging exercises based on input parameters"""
        print("Exercise Generator: Creating debugging exercises...")
        print("=" * 60)
        
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
        
        # Create team with exercise generator
        team = RoundRobinGroupChat([self.exercise_generator], termination_condition=termination)
        
        # Calculate difficulty distribution based on specified difficulty level
        if difficulty_level.lower() == "easy":
            difficulty_dist = {"Easy": num_questions, "Medium": 0, "Hard": 0}
        elif difficulty_level.lower() == "medium":
            difficulty_dist = {"Easy": 0, "Medium": num_questions, "Hard": 0}
        elif difficulty_level.lower() == "hard":
            difficulty_dist = {"Easy": 0, "Medium": 0, "Hard": num_questions}
        else:  # Mixed or default
            # Calculate based on duration and number of questions
            avg_time_per_question = duration_minutes / num_questions if num_questions > 0 else 15
            
            if avg_time_per_question <= 10:
                difficulty_dist = {"Easy": num_questions, "Medium": 0, "Hard": 0}
            elif avg_time_per_question <= 20:
                difficulty_dist = {"Easy": max(0, num_questions - 1), "Medium": 1, "Hard": 0}
            elif avg_time_per_question <= 30:
                difficulty_dist = {"Easy": max(0, num_questions - 2), "Medium": min(2, num_questions), "Hard": 0}
            else:
                difficulty_dist = {"Easy": max(0, num_questions - 3), "Medium": min(2, num_questions), "Hard": min(1, num_questions)}
        
        task = f"""
        Generate {num_questions} debugging exercises with these parameters:
        
        Topics: {', '.join(topics)}
        Concepts: {', '.join(concepts)}
        Number of Questions: {num_questions}
        Total Duration: {duration_minutes} minutes
        Difficulty Level: {difficulty_level}
        Difficulty Distribution: {difficulty_dist}
        
        Create comprehensive, educational debugging exercises that:
        - Are appropriate for the specified difficulty distribution
        - Focus on the requested topics and concepts
        - Provide realistic debugging scenarios
        - Include progressive hints and clear learning objectives
        - Use realistic, educational code examples
        - Fit within the specified time constraints
        
        Please create the exercises in the specified JSON format.
        """
        
        # Run the team and collect result
        result = await team.run(task=task)
        
        # Extract the JSON content from the result
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "exercise_generator":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                # Remove markdown code block formatting if present
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        
        print("Generated Exercises:")
        print(json_content)
        
        try:
            # Parse the JSON to validate it
            exercises_data = json.loads(json_content)
            return exercises_data
        except json.JSONDecodeError as e:
            print(f"Error parsing generated JSON: {e}")
            return {"error": "Failed to generate valid JSON", "raw_content": json_content}
    
    async def calibrate_difficulty(self, exercises_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate the difficulty level of generated exercises"""
        print("\nDifficulty Calibrator: Analyzing exercise difficulty...")
        print("=" * 60)
        
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
        
        # Create team with difficulty calibrator
        team = RoundRobinGroupChat([self.difficulty_calibrator], termination_condition=termination)
        
        task = f"""
        Please analyze and calibrate the difficulty level of these debugging exercises:
        
        {json.dumps(exercises_data, indent=2)}
        
        Provide detailed feedback on:
        - Current difficulty assessment for each exercise
        - Whether the difficulty matches the stated level
        - Time distribution analysis
        - Recommended adjustments if needed
        - Specific suggestions for improvement
        - Justification for difficulty levels
        
        Be thorough and specific in your analysis.
        """
        
        # Run the team and collect result
        result = await team.run(task=task)
        
        # Extract the feedback content from the result
        feedback_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "difficulty_calibrator":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                feedback_content += content
        
        print("Difficulty Calibration:")
        print(feedback_content)
        
        return {
            "exercises": exercises_data,
            "calibration_feedback": feedback_content
        }

    async def generate_exercises_with_calibration(self, topics: List[str], concepts: List[str], num_questions: int, duration_minutes: int, difficulty_level: str = "Mixed") -> Dict[str, Any]:
        """Generate exercises with calibration verification"""
        print("Exercise Generator: Creating exercises with calibration verification...")
        print("=" * 60)
        
        # Generate initial exercises
        current_exercises = await self.generate_exercises(topics, concepts, num_questions, duration_minutes, difficulty_level)
        
        if "error" in current_exercises:
            return current_exercises
        
        # Get calibration feedback
        calibration_result = await self.calibrate_difficulty(current_exercises)
        calibration_feedback = calibration_result.get("calibration_feedback", "")
        
        # Check if calibration agent approves
        if self._is_calibration_approved(calibration_feedback):
            print("Calibration approved!")
            return calibration_result
        else:
            print("Calibration not approved. Refining exercises...")
            # Refine exercises based on calibration feedback
            refined_exercises = await self.refine_exercises_with_feedback(current_exercises, topics, concepts, num_questions, duration_minutes, difficulty_level)
            
            if "error" in refined_exercises:
                return refined_exercises
            
            # Get final calibration
            final_result = await self.calibrate_difficulty(refined_exercises)
            return final_result
    
    async def refine_exercises_with_feedback(self, current_exercises: Dict[str, Any], topics: List[str], concepts: List[str], num_questions: int, duration_minutes: int, difficulty_level: str) -> Dict[str, Any]:
        """Refine exercises based on calibration feedback"""
        print("Refining exercises based on calibration feedback...")
        
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
        
        # Create team with exercise generator
        team = RoundRobinGroupChat([self.exercise_generator], termination_condition=termination)
        
        # Get previous calibration feedback
        previous_feedback = current_exercises.get("calibration_feedback", "")
        
        task = f"""
        Please refine the following debugging exercises based on the calibration feedback:
        
        **Current Exercises:**
        {json.dumps(current_exercises, indent=2)}
        
        **Calibration Feedback:**
        {previous_feedback}
        
        **Original Parameters:**
        Topics: {', '.join(topics)}
        Concepts: {', '.join(concepts)}
        Number of Questions: {num_questions}
        Total Duration: {duration_minutes} minutes
        Difficulty Level: {difficulty_level}
        
        **Refinement Instructions:**
        - Address the specific feedback points mentioned in the calibration
        - Maintain the same number of exercises and overall structure
        - Improve difficulty calibration, time distribution, or educational value as suggested
        - Keep exercises focused on the original topics and concepts
        - Ensure exercises are realistic and educational
        
        Please provide the refined exercises in the same JSON format.
        """
        
        # Run the team and collect result
        result = await team.run(task=task)
        
        # Extract the JSON content from the result
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "exercise_generator":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                # Remove markdown code block formatting if present
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        
        print("Refined Exercises:")
        print(json_content)
        
        try:
            # Parse the JSON to validate it
            refined_exercises = json.loads(json_content)
            
            # Ensure the result has the proper structure
            if "exercises" in refined_exercises:
                return refined_exercises
            else:
                # If the structure is different, wrap it properly
                return {
                    "exercises": refined_exercises,
                    "calibration_feedback": "Refined based on calibration feedback"
                }
        except json.JSONDecodeError as e:
            print(f"Error parsing refined JSON: {e}")
            return {"error": "Failed to generate valid refined JSON", "raw_content": json_content}
    
    def _is_calibration_approved(self, calibration_feedback: str) -> bool:
        """Check if calibration agent approves the exercises"""
        feedback_lower = calibration_feedback.lower()
        
        # Look for explicit APPROVE/REJECT statements
        if "approve" in feedback_lower and "reject" not in feedback_lower:
            return True
        elif "reject" in feedback_lower and "approve" not in feedback_lower:
            return False
        
        # Fallback to keyword analysis if no explicit statements
        approval_keywords = [
            "approved", "satisfied", "appropriate", "good", "excellent", 
            "well-calibrated", "suitable", "acceptable", "meets requirements"
        ]
        
        rejection_keywords = [
            "needs improvement", "too easy", "too hard", "inappropriate", 
            "adjust", "modify", "change", "refine", "not suitable"
        ]
        
        # Count approval and rejection indicators
        approval_count = sum(1 for keyword in approval_keywords if keyword in feedback_lower)
        rejection_count = sum(1 for keyword in rejection_keywords if keyword in feedback_lower)
        
        # Approve if more approval indicators than rejection indicators
        return approval_count > rejection_count
    
    async def generate_exercises_with_human_feedback(self, topics: List[str], concepts: List[str], num_questions: int, duration_minutes: int, difficulty_level: str = "Mixed") -> Dict[str, Any]:
        """Generate exercises with human feedback loop"""
        print("Exercise Generator: Creating exercises with human feedback...")
        print("=" * 60)
        
        # Step 1: Generate exercises with calibration
        result = await self.generate_exercises_with_calibration(topics, concepts, num_questions, duration_minutes, difficulty_level)
        
        if "error" in result:
            return result
        
        # Step 2: Human feedback loop
        while True:
            # Show generated exercises to human
            print("\n" + "="*60)
            print("GENERATED EXERCISES - HUMAN REVIEW")
            print("="*60)
            
            # Handle different possible structures of the result
            if "exercises" in result and isinstance(result["exercises"], dict) and "exercises" in result["exercises"]:
                exercises = result["exercises"]["exercises"]
            elif "exercises" in result and isinstance(result["exercises"], list):
                exercises = result["exercises"]
            else:
                exercises = []
                
            for i, exercise in enumerate(exercises, 1):
                print(f"\nExercise {i}: {exercise.get('title', 'Unknown')}")
                print(f"Difficulty: {exercise.get('difficulty', 'Unknown')}")
                print(f"Description: {exercise.get('description', 'No description')}")
                print(f"Technology: {exercise.get('technology', 'Unknown')}")
                print(f"Estimated Time: {exercise.get('estimatedTime', 'Unknown')} minutes")
                print("-" * 40)
            
            # Get human feedback
            print("\nWhat would you like to do?")
            print("1. Approve (type 'approve')")
            print("2. Request changes (type 'change')")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == "approve":
                print("Exercises approved by human reviewer!")
                # Ensure consistent structure before returning
                if isinstance(result, list):
                    # If result is a list, wrap it in a dictionary with 'exercises' key
                    return {"exercises": result}
                elif isinstance(result, dict):
                    if "exercises" in result:
                        if isinstance(result["exercises"], list):
                            # If result["exercises"] is a list, ensure it's properly wrapped
                            return {"exercises": result["exercises"]}
                        elif isinstance(result["exercises"], dict) and "exercises" in result["exercises"]:
                            # If result["exercises"]["exercises"] exists, extract it
                            return {"exercises": result["exercises"]["exercises"]}
                    # If result is already a dict with proper structure, return it
                return result
            
            elif choice == "change":
                # Get specific feedback
                print("\nPlease provide specific feedback for modifications:")
                feedback = input("Enter your feedback: ").strip()
                
                if feedback:
                    # Refine exercises based on human feedback
                    refined_result = await self.refine_exercises_with_human_feedback(result, topics, concepts, num_questions, duration_minutes, difficulty_level, feedback)
                    if "error" not in refined_result:
                        result = refined_result
                        print("\nExercises have been refined based on your feedback.")
                    else:
                        print(f"Error refining exercises: {refined_result.get('error', 'Unknown error')}")
                        continue
                else:
                    print("No feedback provided. Please try again.")
                    continue
            
            else:
                print("Invalid choice. Please enter 'approve' or 'change'.")
                continue
        
        return result
    
    async def refine_exercises_with_human_feedback(self, current_exercises: Dict[str, Any], topics: List[str], concepts: List[str], num_questions: int, duration_minutes: int, difficulty_level: str, human_feedback: str) -> Dict[str, Any]:
        """Refine exercises based on human feedback"""
        print("Refining exercises based on human feedback...")
        
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
        
        # Create team with exercise generator
        team = RoundRobinGroupChat([self.exercise_generator], termination_condition=termination)
        
        task = f"""
        Please refine the following debugging exercises based on the human feedback:
        
        **Current Exercises:**
        {json.dumps(current_exercises, indent=2)}
        
        **Human Feedback:**
        {human_feedback}
        
        **Original Parameters:**
        Topics: {', '.join(topics)}
        Concepts: {', '.join(concepts)}
        Number of Questions: {num_questions}
        Total Duration: {duration_minutes} minutes
        Difficulty Level: {difficulty_level}
        
        **Refinement Instructions:**
        - Address the specific feedback points mentioned by the human reviewer
        - Maintain the same number of exercises and overall structure
        - Improve the exercises based on the human suggestions
        - Keep exercises focused on the original topics and concepts
        - Ensure exercises are realistic and educational
        
        Please provide the refined exercises in the same JSON format.
        """
        
        # Run the team and collect result
        result = await team.run(task=task)
        
        # Extract the JSON content from the result
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "exercise_generator":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                # Remove markdown code block formatting if present
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        
        print("Refined Exercises (Human Feedback):")
        print(json_content)
        
        try:
            # Parse the JSON to validate it
            refined_exercises = json.loads(json_content)
            
            # Ensure the result has the proper structure
            if "exercises" in refined_exercises:
                return refined_exercises
            else:
                # If the structure is different, wrap it properly
                return {
                    "exercises": refined_exercises,
                    "calibration_feedback": "Refined based on human feedback"
                }
        except json.JSONDecodeError as e:
            print(f"Error parsing refined JSON: {e}")
            return {"error": "Failed to generate valid refined JSON", "raw_content": json_content}

async def generate_debug_exercises(topics: List[str], concepts: List[str], num_questions: int, duration_minutes: int, difficulty_level: str = "Mixed") -> Dict[str, Any]:
    """Main function to generate debugging exercises with the specified parameters"""
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not azure_api_key or azure_api_key == "<your_azure_openai_api_key_here>":
        return {"error": "Please set your Azure OpenAI API key in the .env file"}

    # Define the model client
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"), # For key-based authentication.
    )

    # Create the debugging exercise generator
    generator = DebugExerciseGenerator(model_client)
    
    try:
        # Generate exercises with calibration and human feedback
        result = await generator.generate_exercises_with_human_feedback(topics, concepts, num_questions, duration_minutes, difficulty_level)
        return result
    except Exception as e:
        return {"error": f"Error generating exercises: {str(e)}"}
    finally:
        await model_client.close()

# Main function with human input
async def main():
    """Main function to generate debugging exercises with human input"""
    print("Debug Exercise Generator")
    print("=" * 60)
    
    # Get input from user
    print("Please provide exercise parameters:")
    topics_input = input("Enter topics (comma-separated, e.g., 'React, Python, Node.js'): ").strip()
    concepts_input = input("Enter concepts (comma-separated, e.g., 'State Management, Memory Leaks'): ").strip()
    num_questions = int(input("Number of questions: ").strip())
    duration_minutes = int(input("Duration in minutes: ").strip())
    difficulty_level = input("Enter difficulty level (Easy/Medium/Hard/Mixed): ").strip() or "Mixed"
    
    # Parse inputs
    topics = [topic.strip() for topic in topics_input.split(',') if topic.strip()]
    concepts = [concept.strip() for concept in concepts_input.split(',') if concept.strip()]
    
    print(f"\nGenerating {num_questions} exercises for {duration_minutes} minutes")
    print(f"Topics: {', '.join(topics)}")
    print(f"Concepts: {', '.join(concepts)}")
    print(f"Difficulty Level: {difficulty_level}")
    
    result = await generate_debug_exercises(topics, concepts, num_questions, duration_minutes, difficulty_level)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nGenerated Exercises:")
        print(json.dumps(result, indent=2))
        
        # Save to file
        filename = f"debug_exercises_{num_questions}q_{duration_minutes}min.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nExercises saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
