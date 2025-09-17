import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

load_dotenv()

class DebugExerciseGenerator:
    """Agent for generating debugging exercises based on topics, concepts, number of questions, duration, and experience level"""

    DEFAULT_NUM_QUESTIONS = 5
    DEFAULT_DURATION_MINUTES = 15

    EXPERIENCE_DIFFICULTY_MAP = {
        "beginner": {"Easy": 4, "Medium": 1, "Hard": 0},
        "intermediate": {"Easy": 2, "Medium": 3, "Hard": 0},
        "advanced": {"Easy": 1, "Medium": 2, "Hard": 2}
    }

    def __init__(self, model_client):
        self.model_client = model_client
        self.exercise_generator = self._create_exercise_generator()
        self.difficulty_calibrator = self._create_difficulty_calibrator()

    def _get_difficulty_distribution(self, experience_level: str, num_questions: int) -> Dict[str, int]:
        level = experience_level.strip().upper()
        dist = self.EXPERIENCE_DIFFICULTY_MAP.get(level, {"Easy": num_questions, "Medium": 0, "Hard": 0})
        total = sum(dist.values())
        if total != num_questions:
            easy = int(round(dist.get("Easy", 0) * num_questions / total))
            medium = int(round(dist.get("Medium", 0) * num_questions / total))
            hard = num_questions - easy - medium
            dist = {"Easy": easy, "Medium": medium, "Hard": hard}
        return dist

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

    async def generate_exercises(self, topics: List[str], concepts: List[str], num_questions: int,
                                 duration_minutes: int, difficulty_level: str = "Mixed") -> Dict[str, Any]:
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
                difficulty_dist = {"Easy": max(0, num_questions - 3), "Medium": min(2, num_questions),
                                   "Hard": min(1, num_questions)}

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

    async def generate_exercises_with_calibration(
        self,
        topics: List[str],
        concepts: List[str],
        experience_level: str = "beginner"
    ) -> Dict[str, Any]:
        """Fully automated: generate, calibrate, refine if needed, return final result."""
        print("Exercise Generator: Creating exercises with calibration verification...")
        print("=" * 60)

        num_questions = self.DEFAULT_NUM_QUESTIONS
        duration_minutes = self.DEFAULT_DURATION_MINUTES

        # Generate initial exercises
        current_exercises = await self.generate_exercises(
            topics, concepts, num_questions, duration_minutes, experience_level
        )

        if "error" in current_exercises:
            return current_exercises

        # Get calibration feedback
        calibration_result = await self.calibrate_difficulty(current_exercises)
        calibration_feedback = calibration_result.get("calibration_feedback", "")

        # If calibration is not approved, refine automatically
        attempts = 0
        while not self._is_calibration_approved(calibration_feedback) and attempts < 2:
            print("Calibration not approved. Refining exercises automatically...")
            refined_exercises = await self.refine_exercises_with_feedback(
                calibration_result, topics, concepts, num_questions, duration_minutes, experience_level
            )
            if "error" in refined_exercises:
                return refined_exercises
            calibration_result = await self.calibrate_difficulty(refined_exercises)
            calibration_feedback = calibration_result.get("calibration_feedback", "")
            attempts += 1

        print("Calibration approved or max attempts reached.")
        return calibration_result

    async def refine_exercises_with_feedback(
        self,
        current_exercises: Dict[str, Any],
        topics: List[str],
        concepts: List[str],
        num_questions: int,
        duration_minutes: int,
        experience_level: str
    ) -> Dict[str, Any]:
        """Refine exercises based on calibration feedback (automated, no human input)."""
        print("Refining exercises based on calibration feedback...")

        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([self.exercise_generator], termination_condition=termination)
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
        Experience Level: {experience_level}

        **Refinement Instructions:**
        - Address the specific feedback points mentioned in the calibration
        - Maintain the same number of exercises and overall structure
        - Improve difficulty calibration, time distribution, or educational value as suggested
        - Keep exercises focused on the original topics and concepts
        - Ensure exercises are realistic and educational

        Please provide the refined exercises in the same JSON format.
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

        print("Refined Exercises:")
        print(json_content)

        try:
            refined_exercises = json.loads(json_content)
            if "exercises" in refined_exercises:
                return refined_exercises
            else:
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


async def generate_exercises(tech_stack: str, topics: List[str], level: str):
    """Function to generate Debug Exercises based on a technical stack"""
    try:
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )

        exercise_generator = DebugExerciseGenerator(model_client)
        generated_exercise = await exercise_generator.generate_exercises_with_calibration([tech_stack], topics, level)
        return generated_exercise

    except Exception as e:
        print('Error generating debug exercises:', e)

if __name__ == "__main__":
    import asyncio

    try:
        print('Generating debug exercises.....')
        exercises = asyncio.run(generate_exercises(
            'Python',
            ['File Handling', 'Loops', 'os', 'Control statement', 'OOPs'],
            'INTERMEDIATE'
        ))
        if exercises:
            print("Generated debug exercises......")
            with open('exercises.json', 'w') as outfile:
                json.dump(exercises, outfile, indent=2)
            print('Saved debug exercises......')
        else:
            raise Exception("Failed to generate debug exercises")

    except Exception as e:
        print('Unable to generate the exercises', e)
