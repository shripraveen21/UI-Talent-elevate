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

class DebugAnswerEvaluator:
    """Agent for evaluating debugging exercise answers and providing detailed feedback"""
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.solution_validator = self._create_solution_validator()
        self.feedback_provider = self._create_feedback_provider()
        self.scoring_agent = self._create_scoring_agent()
        self.solution_checker = self._create_solution_checker()
    
    def _create_solution_validator(self):
        """Creates the Solution Validation Agent"""
        system_message = """
        You are an expert Solution Validator specializing in:
        - Code correctness verification
        - Solution completeness assessment
        - Alternative solution identification
        - Solution quality evaluation
        
        Your role is to validate debugging solutions and provide detailed technical feedback.
        
        **Validation Criteria:**
        1. **Correctness:**
           - Does the solution fix the identified bug?
           - Are there any new bugs introduced?
           - Does the code work as expected?
           - Are edge cases handled properly?
        
        2. **Completeness:**
           - Are all aspects of the problem addressed?
           - Is the solution comprehensive?
           - Are all bugs in the original code fixed?
        
        3. **Quality:**
           - Is the code clean and readable?
           - Are best practices followed?
           - Is the solution efficient?
           - Is the code maintainable?
        
        4. **Alternative Solutions:**
           - Are there other valid approaches?
           - What are the trade-offs?
           - Which solution is best and why?
        
        **Validation Process:**
        1. **Test the solution** against the problem description
        2. **Check for correctness** and completeness
        3. **Evaluate code quality** and best practices
        4. **Identify alternatives** if applicable
        5. **Provide specific feedback** on improvements
        
        **Feedback Format:**
        - Overall assessment (Valid/Partially Valid/Invalid)
        - Specific issues found
        - Suggestions for improvement
        - Alternative solutions (if any)
        - Code quality recommendations
        - Technical accuracy notes
        
        Be thorough, constructive, and specific in your validation.
        End your response with "TERMINATE".
        """
        
        return AssistantAgent(
            name="solution_validator",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
    
    def _create_feedback_provider(self):
        """Creates the Feedback Provider Agent"""
        system_message = """
        You are an expert Feedback Provider specializing in:
        - Educational feedback design
        - Learning guidance
        - Constructive criticism
        - Skill development recommendations
        
        Your role is to provide helpful, educational feedback for debugging solutions.
        
        **Feedback Guidelines:**
        1. **Educational Focus:** Help the learner understand the concepts
        2. **Constructive Tone:** Be encouraging while pointing out areas for improvement
        3. **Specific Examples:** Provide concrete suggestions and examples
        4. **Learning Path:** Guide toward better understanding and skills
        
        **Feedback Structure:**
        - **Strengths:** What the learner did well
        - **Areas for Improvement:** Specific areas that need work
        - **Learning Opportunities:** Concepts to study further
        - **Next Steps:** Recommended actions for improvement
        - **Resources:** Suggested learning materials or practices
        
        **Feedback Quality:**
        - **Specific:** Point to exact lines or concepts
        - **Actionable:** Provide clear steps for improvement
        - **Encouraging:** Maintain a positive, supportive tone
        - **Educational:** Focus on learning and skill development
        
        Provide feedback that helps learners grow and improve their debugging skills.
        End your response with "TERMINATE".
        """
        
        return AssistantAgent(
            name="feedback_provider",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
    
    def _create_scoring_agent(self):
        """Creates the Scoring Agent"""
        system_message = """
        You are an expert Scoring Agent specializing in:
        - Technical assessment scoring
        - Performance evaluation
        - Skill level determination
        - Progress tracking
        
        Your role is to provide accurate scoring and assessment for debugging solutions.
        
        **Scoring Criteria:**
        1. **Correctness (40%):**
           - Does the solution fix the bug?
           - Are all issues resolved?
           - Is the code functional?
        
        2. **Code Quality (25%):**
           - Is the code clean and readable?
           - Are best practices followed?
           - Is the solution efficient?
        
        3. **Completeness (20%):**
           - Are all aspects addressed?
           - Is the solution comprehensive?
           - Are edge cases handled?
        
        4. **Learning Application (15%):**
           - Does it show understanding of concepts?
           - Are debugging techniques applied correctly?
           - Is the approach logical?
        
        **Scoring Scale:**
        - **Excellent (90-100):** Perfect or near-perfect solution
        - **Good (80-89):** Solid solution with minor issues
        - **Satisfactory (70-79):** Adequate solution with some problems
        - **Needs Improvement (60-69):** Solution has significant issues
        - **Inadequate (0-59):** Solution doesn't meet requirements
        
        **Score Breakdown:**
        Provide detailed scores for each criterion and overall score.
        Include specific justifications for the scores given.
        
        Be fair, accurate, and constructive in your scoring.
        
        IMPORTANT CONSISTENCY RULE:
        If the Solution Checker marks the solution as EXACT_MATCH with HIGH confidence, 
        you MUST give full marks (100 overall, Grade A).
        If the Solution Checker returns PARTIAL_MATCH but your assessment is 100, 
        normalize correctness to 100 and treat it as EXACT_MATCH.
        
        Avoid producing contradictory results between scoring and correctness check.
        
        End your response with "TERMINATE".
        """
        
        return AssistantAgent(
            name="scoring_agent",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
    
    def _create_solution_checker(self):
        """Creates the Solution Checker Agent"""
        system_message = """
        You are an expert Solution Checker specializing in:
        - Verifying if user solutions achieve the desired functional outcome
        - Identifying functionally equivalent solutions regardless of implementation approach
        - Assessing solution correctness based on problem requirements
        - Providing accurate functional correctness assessment
        
        Your role is to check if the user's solution is functionally correct by analyzing whether it solves the problem, regardless of how it's implemented.
        
        **Functional Assessment Process:**
        1. **Problem Analysis:** Understand what the exercise is trying to achieve
        2. **Solution Validation:** Check if the user's solution addresses the core problem
        3. **Functional Equivalence:** Verify the solution produces the expected outcome
        4. **Edge Case Handling:** Ensure the solution handles various scenarios
        5. **No New Bugs:** Confirm the solution doesn't introduce new issues
        
        **Assessment Criteria:**
        - **FUNCTIONALLY_CORRECT:** Solution achieves the desired outcome using any valid approach
        - **PARTIALLY_CORRECT:** Solution addresses most of the problem but has minor issues
        - **INCORRECT:** Solution fails to solve the problem or introduces new bugs
        
        **Output Format:**
        Provide a simple assessment in this EXACT format:
        
        CORRECTNESS: [FUNCTIONALLY_CORRECT/PARTIALLY_CORRECT/INCORRECT]
        CONFIDENCE: [HIGH/MEDIUM/LOW]
        SCORE: [0-100]
        
        Then provide detailed analysis.
        
        **Key Principles:**
        - Focus on FUNCTIONAL CORRECTNESS, not code similarity
        - Accept different implementation approaches if they solve the problem
        - Consider alternative algorithms, data structures, or coding styles as valid
        - Only mark as incorrect if the solution fails to achieve the desired outcome
        - Give full credit (100) for functionally correct solutions regardless of approach
        
        **Examples of Valid Different Approaches:**
        - Using different variable names or function names
        - Using different algorithms (e.g., iterative vs recursive)
        - Using different data structures (e.g., array vs list)
        - Using different coding styles or patterns
        - Using different libraries or frameworks (if appropriate)
        
        Be fair and focus on whether the solution WORKS, not how it looks.
        
        End your response with "TERMINATE".
        """
        
        return AssistantAgent(
            name="solution_checker",
            model_client=self.model_client,
            system_message=system_message,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
    
    async def evaluate_single_answer(self, exercise: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
        """Evaluate a single debugging exercise answer"""
        print(f"Evaluating answer for exercise: {exercise.get('title', 'Unknown')}")
        print("=" * 60)
        
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
        
        # Create team with solution validator
        team = RoundRobinGroupChat([self.solution_validator], termination_condition=termination)
        
        task = f"""
        Please evaluate this debugging solution:
        
        **Exercise:**
        Title: {exercise.get('title', 'N/A')}
        Description: {exercise.get('description', 'N/A')}
        Technology: {exercise.get('technology', 'N/A')}
        Difficulty: {exercise.get('difficulty', 'N/A')}
        Expected Behavior: {exercise.get('expectedBehavior', 'N/A')}
        Current Behavior: {exercise.get('currentBehavior', 'N/A')}
        Original Code:
        {exercise.get('code', 'N/A')}
        
        **User's Solution:**
        {user_answer}
        
        **Correct Solution:**
        {exercise.get('solution', 'N/A')}
        
        Provide detailed evaluation including:
        - Correctness assessment
        - Code quality analysis
        - Completeness check
        - Alternative solutions (if any)
        - Specific improvements needed
        """
        
        # Run the team and collect result
        result = await team.run(task=task)
        
        # Extract the validation content from the result
        validation_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "solution_validator":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                validation_content += content
        
        return validation_content
    
    async def get_detailed_feedback(self, exercise: Dict[str, Any], user_answer: str, validation: str) -> str:
        """Get detailed educational feedback for the solution"""
        print("Generating detailed feedback...")
        print("=" * 60)
        
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
        
        # Create team with feedback provider
        team = RoundRobinGroupChat([self.feedback_provider], termination_condition=termination)
        
        task = f"""
        Please provide detailed educational feedback for this debugging solution:
        
        **Exercise:**
        {json.dumps(exercise, indent=2)}
        
        **User's Solution:**
        {user_answer}
        
        **Technical Validation:**
        {validation}
        
        Provide comprehensive feedback including:
        - Strengths of the solution
        - Areas for improvement
        - Learning opportunities
        - Next steps for skill development
        - Recommended resources or practices
        """
        
        # Run the team and collect result
        result = await team.run(task=task)
        
        # Extract the feedback content from the result
        feedback_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "feedback_provider":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                feedback_content += content
        
        return feedback_content
    
    async def calculate_score(self, exercise: Dict[str, Any], user_answer: str, validation: str) -> Dict[str, Any]:
        """Calculate detailed score for the solution"""
        print("Calculating detailed score...")
        print("=" * 60)
        
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
        
        # Create team with scoring agent
        team = RoundRobinGroupChat([self.scoring_agent], termination_condition=termination)
        
        task = f"""
        Please calculate a detailed score for this debugging solution:
        
        **Exercise:**
        {json.dumps(exercise, indent=2)}
        
        **User's Solution:**
        {user_answer}
        
        **Technical Validation:**
        {validation}
        
        Provide detailed scoring in the following EXACT format:
        Correctness Score: [0-100]
        Code Quality Score: [0-100]
        Completeness Score: [0-100]
        Learning Application Score: [0-100]
        Overall Score: [0-100]
        Grade: [A/B/C/D/F]
        
        Then provide detailed justification for each score.
        """
        
        # Run the team and collect result
        result = await team.run(task=task)
        
        # Extract the scoring content from the result
        scoring_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "scoring_agent":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                scoring_content += content
        
        return scoring_content
    
    async def check_solution_correctness(self, user_answer: str, reference_solution: str, exercise: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if the user's solution matches the correct solution"""
        print("Checking solution correctness...")
        print("=" * 60)
        
        # Create termination condition
        termination = TextMentionTermination("TERMINATE")
        
        # Create team with solution checker
        team = RoundRobinGroupChat([self.solution_checker], termination_condition=termination)
        
        # Build exercise context if available
        exercise_context = ""
        if exercise:
            exercise_context = f"""
        **Exercise Context:**
        Title: {exercise.get('title', 'N/A')}
        Description: {exercise.get('description', 'N/A')}
        Expected Behavior: {exercise.get('expectedBehavior', 'N/A')}
        Current Behavior: {exercise.get('currentBehavior', 'N/A')}
        Technology: {exercise.get('technology', 'N/A')}
        Difficulty: {exercise.get('difficulty', 'N/A')}
        """
        
        task = f"""
        Please check if the user's solution is functionally correct:
        
        {exercise_context}
        **User's Solution:**
        {user_answer}
        
        **Reference Solution (for context only):**
        {reference_solution}
        
        **Assessment Instructions:**
        - Focus on whether the user's solution achieves the same functional outcome
        - Accept different implementation approaches if they solve the problem correctly
        - Consider alternative algorithms, data structures, or coding styles as valid
        - Only mark as incorrect if the solution fails to achieve the desired outcome
        - Give full credit (100) for functionally correct solutions regardless of approach
        
        Provide assessment in the exact format specified.
        """
        
        # Run the team and collect result
        result = await team.run(task=task)
        
        # Extract the checking content from the result
        checking_content = ""
        for message in result.messages:
            if isinstance(message, TextMessage) and message.source == "solution_checker":
                content = message.content
                # Remove TERMINATE if present
                if "TERMINATE" in content:
                    content = content.replace("TERMINATE", "").strip()
                checking_content += content
        
        # Extract correctness information
        correctness_info = self._extract_correctness_info(checking_content)
        
        return {
            "status": correctness_info["correctness"],
            "confidence": correctness_info["confidence"],
            "score": correctness_info["score"],
            "details": checking_content
        }
    
    def _extract_correctness_info(self, checking_text: str) -> Dict[str, Any]:
        """Extract correctness information from checking text"""
        import re
        
        # Extract correctness
        correctness_match = re.search(r'CORRECTNESS:\s*(\w+)', checking_text, re.IGNORECASE)
        correctness = correctness_match.group(1) if correctness_match else "INCORRECT"
        
        # Extract confidence
        confidence_match = re.search(r'CONFIDENCE:\s*(\w+)', checking_text, re.IGNORECASE)
        confidence = confidence_match.group(1) if confidence_match else "LOW"
        
        # Extract score
        score_match = re.search(r'SCORE:\s*(\d+)', checking_text, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 0
        
        return {
            "correctness": correctness,
            "confidence": confidence,
            "score": score
        }
    
    async def evaluate_answers(self, exercises_data: Dict[str, Any], user_answers: Dict[str, str]) -> Dict[str, Any]:
        """Evaluate user answers for debugging exercises"""
        try:
            exercises = exercises_data.get("exercises", [])
            
            if not exercises:
                return {"error": "No exercises found in the provided data"}
            
            if not user_answers:
                return {"error": "No user answers provided"}
            
            results = []
            total_score = 0
            total_exercises = len(exercises)
            
            for exercise in exercises:
                exercise_id = exercise.get("id", "")
                user_answer = user_answers.get(exercise_id, "")
                reference_solution = exercise.get("solution", "")
                
                if not user_answer:
                    results.append({
                        "exercise_id": exercise_id,
                        "title": exercise.get("title", ""),
                        "score": 0,
                        "grade": "F",
                        "status": "INCORRECT",
                        "confidence": "LOW",
                        "correctness": {
                            "score": 0,
                            "status": "MISMATCH",
                            "details": "No answer provided"
                        },
                        "scoring_breakdown": {
                            "correctness": 0,
                            "code_quality": 0,
                            "completeness": 0,
                            "learning_application": 0
                        },
                        "feedback": {
                            "strengths": [],
                            "areas_for_improvement": ["Provide a solution to the exercise"],
                            "Learning_Opportunities": ["Review the exercise requirements"],
                            "next_steps": ["Attempt to solve the exercise"],
                            "resources": []
                        },
                        "validation": "No answer provided",
                        "hints_used": 0
                    })
                    continue
                
                # FIRST: Check if solution is functionally correct
                correctness_check = await self.check_solution_correctness(user_answer, reference_solution, exercise)
                
                # If solution is functionally correct, assign full marks
                if (correctness_check.get("status") in ["FUNCTIONALLY_CORRECT"] and 
                    correctness_check.get("confidence") in ["HIGH", "MEDIUM"]):
                    
                    results.append({
                        "exercise_id": exercise_id,
                        "title": exercise.get("title", ""),
                        "score": 100,
                        "grade": "A",
                        "status": "CORRECT",
                        "confidence": "HIGH",
                        "correctness": {
                            "score": 100,
                            "status": correctness_check.get("status", "FUNCTIONALLY_CORRECT"),
                            "details": correctness_check.get("details", "Solution is functionally correct and achieves the desired outcome")
                        },
                        "scoring_breakdown": {
                            "correctness": 100,
                            "code_quality": 100,
                            "completeness": 100,
                            "learning_application": 100
                        },
                        "feedback": {
                            "strengths": ["Solution is functionally correct", "Achieves the desired outcome", "Proper implementation approach"],
                            "areas_for_improvement": [],
                            "Learning_Opportunities": [],
                            "next_steps": [],
                            "resources": []
                        },
                        "validation": "No major issues found",
                        "hints_used": 0
                    })
                    total_score += 100
                    continue
                
                # ONLY if solution is not functionally correct, apply detailed validation
                print(f"Solution not functionally correct - applying detailed validation for {exercise_id}")
                
                # Evaluate the answer with detailed validation
                validation = await self.evaluate_single_answer(exercise, user_answer)
                
                # Get detailed feedback
                feedback = await self.get_detailed_feedback(exercise, user_answer, validation)
                
                # Calculate score
                scoring = await self.calculate_score(exercise, user_answer, validation)
                
                # Extract numeric score from scoring text
                score = self._extract_score_from_text(scoring)
                
                # Determine status based on score
                if score >= 90:
                    status = "CORRECT"
                elif score >= 60:
                    status = "PARTIALLY_CORRECT"
                else:
                    status = "INCORRECT"
                
                # Determine confidence based on correctness status
                correctness_status = correctness_check.get("status", "MISMATCH")
                if correctness_status == "EXACT_MATCH":
                    confidence = "HIGH"
                elif correctness_status == "PARTIAL_MATCH":
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"
                
                # Parse feedback into structured format
                structured_feedback = self._parse_feedback_into_structure(feedback)
                
                result = {
                    "exercise_id": exercise_id,
                    "title": exercise.get("title", ""),
                    "score": score,
                    "grade": self._calculate_grade(score),
                    "status": status,
                    "confidence": confidence,
                    "correctness": {
                        "score": correctness_check.get("score", 0),
                        "status": correctness_status,
                        "details": correctness_check.get("details", "Solution analysis completed")
                    },
                    "scoring_breakdown": self._extract_scoring_breakdown(scoring),
                    "feedback": structured_feedback,
                    "validation": validation,
                    "hints_used": 0  # This would need to be tracked if hints are implemented
                }
                
                results.append(result)
                total_score += score
            
            # Post-processing: Ensure consistency between correctness_check and scoring
            results = self._normalize_consistency(results)
            
            # Recalculate total score after normalization
            total_score = sum(result["score"] for result in results)
            
            # Calculate overall results
            average_score = total_score / total_exercises if total_exercises > 0 else 0
            overall_grade = self._calculate_grade(average_score)
            
            # Sort results by exercise_id for consistency
            results.sort(key=lambda x: x.get("exercise_id", ""))
            
            return {
                "overall_score": average_score,
                "overall_grade": overall_grade,
                "total_exercises": total_exercises,
                "results": results,
                "summary": {
                    "correct_solutions": len([r for r in results if r.get("status") == "CORRECT"]),
                    "partially_correct_solutions": len([r for r in results if r.get("status") == "PARTIALLY_CORRECT"]),
                    "incorrect_solutions": len([r for r in results if r.get("status") == "INCORRECT"]),
                    "average_score": average_score
                }
            }
            
        except Exception as e:
            return {"error": f"Error during evaluation: {str(e)}"}
    
    def _extract_score_from_text(self, scoring_text: str) -> int:
        """Extract numeric score from scoring text using multiple patterns"""
        import re
        
        # Try multiple patterns to extract the overall score
        patterns = [
            r'Overall Score:\s*(\d+)',
            r'Overall score:\s*(\d+)',
            r'Overall Score\s*\(0-100\):\s*(\d+)',
            r'Overall score\s*\(0-100\):\s*(\d+)',
            r'Overall Score\s*\(0-100\):\s*(\d+)',
            r'Overall\s+Score[:\s]*(\d+)',
            r'Overall\s+score[:\s]*(\d+)',
            r'Score:\s*(\d+)',
            r'score:\s*(\d+)',
            r'(\d+)\s*points?',
            r'(\d+)\s*out\s+of\s+100'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, scoring_text, re.IGNORECASE)
            if match:
                try:
                    score = int(match.group(1))
                    if 0 <= score <= 100:
                        return score
                except ValueError:
                    continue
        
        # If no pattern matches, try to find any number between 0-100
        numbers = re.findall(r'\b(\d+)\b', scoring_text)
        for num_str in numbers:
            try:
                score = int(num_str)
                if 0 <= score <= 100:
                    return score
            except ValueError:
                continue
        
        # Default to 0 if no score found
        return 0
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from numeric score"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _normalize_consistency(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure consistency between correctness_check and scoring results"""
        normalized_results = []
        
        for result in results:
            # Make a copy to avoid modifying the original
            normalized_result = result.copy()
            
            # Get current values
            score = result.get("score", 0)
            correctness = result.get("correctness", {})
            status = correctness.get("status", "MISMATCH")
            confidence = result.get("confidence", "LOW")
            correctness_score = correctness.get("score", 0)
            
            # Consistency Rule 1: If overall_score = 100, correctness_check must be FUNCTIONALLY_CORRECT, HIGH, 100
            if score == 100:
                if status != "FUNCTIONALLY_CORRECT" or confidence != "HIGH" or correctness_score != 100:
                    print(f"Normalizing consistency for {result.get('exercise_id', 'unknown')}: Score=100 but correctness_check inconsistent")
                    normalized_result["status"] = "CORRECT"
                    normalized_result["confidence"] = "HIGH"
                    normalized_result["correctness"] = {
                        "score": 100,
                        "status": "FUNCTIONALLY_CORRECT",
                        "details": correctness.get("details", "") + "\n[Consistency normalized: Score=100 requires FUNCTIONALLY_CORRECT]"
                    }
                    # Update scoring breakdown if it exists
                    if "scoring_breakdown" in normalized_result:
                        normalized_result["scoring_breakdown"] = {
                            "correctness": 100,
                            "code_quality": 100,
                            "completeness": 100,
                            "learning_application": 100
                        }
            
            # Consistency Rule 2: If correctness_check is FUNCTIONALLY_CORRECT with HIGH confidence, score should be 100
            elif status == "FUNCTIONALLY_CORRECT" and confidence == "HIGH" and correctness_score == 100:
                if score != 100:
                    print(f"Normalizing consistency for {result.get('exercise_id', 'unknown')}: FUNCTIONALLY_CORRECT but score={score}")
                    normalized_result["score"] = 100
                    normalized_result["grade"] = "A"
                    normalized_result["status"] = "CORRECT"
                    normalized_result["confidence"] = "HIGH"
                    # Update scoring breakdown if it exists
                    if "scoring_breakdown" in normalized_result:
                        normalized_result["scoring_breakdown"] = {
                            "correctness": 100,
                            "code_quality": 100,
                            "completeness": 100,
                            "learning_application": 100
                        }
                    # Update feedback to reflect normalization
                    if "feedback" in normalized_result and isinstance(normalized_result["feedback"], dict):
                        normalized_result["feedback"]["strengths"] = ["Solution is functionally correct and achieves the desired outcome. [Consistency normalized]"]
            
            # Consistency Rule 3: If PARTIALLY_CORRECT with HIGH confidence and score is 100, treat as FUNCTIONALLY_CORRECT
            elif status == "PARTIALLY_CORRECT" and confidence == "HIGH" and score == 100:
                print(f"Normalizing consistency for {result.get('exercise_id', 'unknown')}: PARTIALLY_CORRECT with score=100, treating as FUNCTIONALLY_CORRECT")
                normalized_result["status"] = "CORRECT"
                normalized_result["confidence"] = "HIGH"
                normalized_result["correctness"] = {
                    "score": 100,
                    "status": "FUNCTIONALLY_CORRECT",
                    "details": correctness.get("details", "") + "\n[Consistency normalized: PARTIALLY_CORRECT with score=100 treated as FUNCTIONALLY_CORRECT]"
                }
            
            normalized_results.append(normalized_result)
        
        return normalized_results
    
    def _parse_feedback_into_structure(self, feedback_text: str) -> Dict[str, List[str]]:
        """Parse feedback text into structured format"""
        # This is a simplified parser - in a real implementation, you might want more sophisticated parsing
        structured = {
            "strengths": [],
            "areas_for_improvement": [],
            "Learning_Opportunities": [],
            "next_steps": [],
            "resources": []
        }
        
        # Basic parsing - look for common patterns in feedback
        lines = feedback_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for section headers
            if any(keyword in line.lower() for keyword in ['strength', 'good', 'well done', 'excellent']):
                current_section = "strengths"
            elif any(keyword in line.lower() for keyword in ['improve', 'issue', 'problem', 'fix', 'better']):
                current_section = "areas_for_improvement"
            elif any(keyword in line.lower() for keyword in ['learn', 'study', 'understand', 'concept']):
                current_section = "Learning_Opportunities"
            elif any(keyword in line.lower() for keyword in ['next', 'step', 'action', 'recommend']):
                current_section = "next_steps"
            elif any(keyword in line.lower() for keyword in ['resource', 'link', 'url', 'documentation']):
                current_section = "resources"
            elif line.startswith('-') or line.startswith('*') or line.startswith('•'):
                # Bullet point - add to current section
                if current_section and current_section in structured:
                    structured[current_section].append(line[1:].strip())
            elif current_section and current_section in structured:
                # Regular line - add to current section
                structured[current_section].append(line)
        
        # If no structured feedback found, provide generic feedback
        if not any(structured.values()):
            structured["areas_for_improvement"] = ["Review the solution and identify areas for improvement"]
            structured["Learning_Opportunities"] = ["Study the debugging concepts covered in this exercise"]
            structured["next_steps"] = ["Practice similar debugging exercises"]
        
        return structured
    
    def _extract_scoring_breakdown(self, scoring_text: str) -> Dict[str, int]:
        """Extract scoring breakdown from scoring text"""
        import re
        
        breakdown = {
            "correctness": 0,
            "code_quality": 0,
            "completeness": 0,
            "learning_application": 0
        }
        
        # Look for scoring patterns
        patterns = {
            "correctness": [r'correctness[:\s]*(\d+)', r'correctness\s*score[:\s]*(\d+)'],
            "code_quality": [r'code\s*quality[:\s]*(\d+)', r'quality[:\s]*(\d+)'],
            "completeness": [r'completeness[:\s]*(\d+)', r'complete[:\s]*(\d+)'],
            "learning_application": [r'learning[:\s]*(\d+)', r'application[:\s]*(\d+)']
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, scoring_text, re.IGNORECASE)
                if match:
                    try:
                        score = int(match.group(1))
                        if 0 <= score <= 100:
                            breakdown[key] = score
                            break
                    except ValueError:
                        continue
        
        # If no breakdown found, use overall score for all categories
        overall_score = self._extract_score_from_text(scoring_text)
        if overall_score > 0 and not any(breakdown.values()):
            breakdown = {
                "correctness": overall_score,
                "code_quality": overall_score,
                "completeness": overall_score,
                "learning_application": overall_score
            }
        
        return breakdown

async def evaluate_debug_answers(exercises_data: Dict[str, Any], user_answers: Dict[str, str]) -> Dict[str, Any]:
    """Main function to evaluate debugging exercise answers"""
    openai_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not openai_key or openai_key == "<your_AZURE_OPENAI_API_KEY_here>":
        return {"error": "Please set your OpenAI API key in the .env file"}

    # Define the model client
    model_client =AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1",
        model="gpt-4.1",
        api_version="2024-06-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_AZURE_OPENAI_API_KEY"), # For key-based authentication.
    )


    # Create the debugging answer evaluator
    evaluator = DebugAnswerEvaluator(model_client)
    
    try:
        # Evaluate the answers
        result = await evaluator.evaluate_answers(exercises_data, user_answers)
        return result
    except Exception as e:
        return {"error": f"Error evaluating answers: {str(e)}"}
    finally:
        await model_client.close()

# Main function with human input
async def main():
    """Main function to evaluate debugging answers with human input"""
    print("Debug Answer Evaluator")
    print("=" * 60)
    
    # Get exercises from user
    print("Please provide the exercises to evaluate:")
    exercises_input = input("Enter exercises JSON (or press Enter to use sample): ").strip()
    
    if exercises_input:
        try:
            exercises_data = json.loads(exercises_input)
        except json.JSONDecodeError:
            print("Invalid JSON format. Using sample exercises.")
            exercises_data = {
                "exercises": {
                    "exercises": [
                        {
                            "id": "exercise_1",
                            "title": "Memory Leak in React Component",
                            "description": "Fix memory leak in React component",
                            "technology": "React 18, JavaScript ES6+",
                            "difficulty": "Medium",
                            "code": "// Original buggy code here",
                            "expectedBehavior": "Component should clean up resources",
                            "currentBehavior": "Memory leak occurs",
                            "solution": "// Correct solution here",
                            "explanation": "Explanation of the fix"
                        }
                    ]
                }
            }
    else:
        # Use sample exercises
        exercises_data = {
            "exercises": {
                "exercises": [
                    {
                        "id": "exercise_1",
                        "title": "Memory Leak in React Component",
                        "description": "Fix memory leak in React component",
                        "technology": "React 18, JavaScript ES6+",
                        "difficulty": "Medium",
                        "code": "// Original buggy code here",
                        "expectedBehavior": "Component should clean up resources",
                        "currentBehavior": "Memory leak occurs",
                        "solution": "// Correct solution here",
                        "explanation": "Explanation of the fix"
                    }
                ]
            }
        }
    
    # Get user answers
    exercises = exercises_data.get("exercises", {}).get("exercises", [])
    print(f"\nPlease provide answers for {len(exercises)} exercises:")
    user_answers = {}
    for i, exercise in enumerate(exercises, 1):
        exercise_id = exercise.get("id", f"exercise_{i}")
        print(f"\nExercise {i}: {exercise.get('title', 'Unknown')}")
        answer = input(f"Enter your solution for exercise {i}: ").strip()
        user_answers[exercise_id] = answer
    
    print(f"\nEvaluating {len(exercises)} answers...")
    
    result = await evaluate_debug_answers(exercises_data, user_answers)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nEvaluation Results:")
        print(json.dumps(result, indent=2))
        
        # Save to file
        filename = f"debug_evaluation_{len(exercises)}_answers.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nEvaluation results saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
