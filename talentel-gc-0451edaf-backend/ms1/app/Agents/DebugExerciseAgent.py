import os
import asyncio
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import UserMessage
from autogen_ext.auth.azure import AzureTokenProvider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage
from autogen_agentchat.ui import Console
# from azure.identity import DefaultAzureCredentia 

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
    
    async def generate_exercises(self, topics: List[str], concepts: List[str], num_questions: int, duration_minutes: int, difficulty: str = None) -> Dict[str, Any]:
        """Generate debugging exercises based on input parameters"""
        print("Exercise Generator: Creating debugging exercises...")
        print("=" * 60)
        
        
        termination = TextMentionTermination("TERMINATE")
        
        
        team = RoundRobinGroupChat([self.exercise_generator], termination_condition=termination)
        
        
        avg_time_per_question = duration_minutes / num_questions if num_questions > 0 else 15
        
        
        if difficulty and difficulty.lower() in ['easy', 'medium', 'hard']:
            
            difficulty_lower = difficulty.lower()
            if difficulty_lower == 'easy':
                difficulty_dist = {"Easy": num_questions, "Medium": 0, "Hard": 0}
            elif difficulty_lower == 'medium':
                difficulty_dist = {"Easy": 0, "Medium": num_questions, "Hard": 0}
            elif difficulty_lower == 'hard':
                difficulty_dist = {"Easy": 0, "Medium": 0, "Hard": num_questions}
        else:
            
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
        Average Time per Question: {avg_time_per_question:.1f} minutes
        Difficulty Level: {difficulty if difficulty else 'Auto-determined based on time'}
        Difficulty Distribution: {difficulty_dist}
        
        Create comprehensive, educational debugging exercises that:
        - Are appropriate for the specified difficulty level and distribution
        - Focus on the requested topics and concepts
        - Provide realistic debugging scenarios
        - Include progressive hints and clear learning objectives
        - Use realistic, educational code examples
        - Fit within the specified time constraints
        - Match the requested difficulty level characteristics
        
        Please create the exercises in the specified JSON format.
        """
        
        
        result = await team.run(task=task)
        
        
        json_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "exercise_generator":
                content = message.content
                
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                
                if content.startswith("```json") and content.endswith("```"):
                    content = content[7:-3].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                json_content += content
        
        print("Generated Exercises:")
        print(json_content)
        
        try:
            
            exercises_data = json.loads(json_content)
            return exercises_data
        except json.JSONDecodeError as e:
            print(f"Error parsing generated JSON: {e}")
            return {"error": "Failed to generate valid JSON", "raw_content": json_content}
    
    async def calibrate_difficulty(self, exercises_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate the difficulty level of generated exercises"""
        print("\nDifficulty Calibrator: Analyzing exercise difficulty...")
        print("=" * 60)
        
        
        termination = TextMentionTermination("TERMINATE")
        
        
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
        
        
        result = await team.run(task=task)
        
        
        feedback_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "difficulty_calibrator":
                content = message.content
                
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                feedback_content += content
        
        print("Difficulty Calibration:")
        print(feedback_content)
        
        return {
            "exercises": exercises_data,
            "calibration_feedback": feedback_content
        }

async def generate_debug_exercises(topics: List[str], concepts: List[str], num_questions: int, duration_minutes: int, difficulty: str = None) -> Dict[str, Any]:
    """Main function to generate debugging exercises with the specified parameters"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "<your_openai_api_key_here>":
        return {"error": "Please set your OpenAI API key in the .env file"}

    
    model_client =  AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"), 
    )



    
    generator = DebugExerciseGenerator(model_client)
    
    try:
        
        exercises_data = await generator.generate_exercises(topics, concepts, num_questions, duration_minutes, difficulty)
        
        if "error" in exercises_data:
            return exercises_data
        
        
        # result = await generator.calibrate_difficulty(exercises_data)
        
        return exercises_data
    except Exception as e:
        return {"error": f"Error generating exercises: {str(e)}"}
    finally:
        await model_client.close()


async def main():
    """Main function to generate debugging exercises with human input"""
    print("Debug Exercise Generator")
    print("=" * 60)
    
    
    print("Please provide exercise parameters:")
    topics_input = input("Enter topics (comma-separated, e.g., 'React, Python, Node.js'): ").strip()
    concepts_input = input("Enter concepts (comma-separated, e.g., 'State Management, Memory Leaks'): ").strip()
    num_questions = int(input("Number of questions: ").strip())
    duration_minutes = int(input("Duration in minutes: ").strip())
    difficulty = input("Difficulty level (Easy/Medium/Hard) or press Enter for auto: ").strip()
    
    topics = [topic.strip() for topic in topics_input.split(',') if topic.strip()]
    concepts = [concept.strip() for concept in concepts_input.split(',') if concept.strip()]
    
    print(f"\nGenerating {num_questions} exercises for {duration_minutes} minutes")
    print(f"Topics: {', '.join(topics)}")
    print(f"Concepts: {', '.join(concepts)}")
    print(f"Difficulty: {difficulty if difficulty else 'Auto-determined'}")
    
    result = await generate_debug_exercises(topics, concepts, num_questions, duration_minutes, difficulty)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nGenerated Exercises:")
        print(json.dumps(result, indent=2))
        
        
        filename = f"debug_exercises_{num_questions}q_{duration_minutes}min.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nExercises saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
