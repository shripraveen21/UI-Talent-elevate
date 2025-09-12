"""
API Wrapper for Debug Exercise System
Simple function calls to the two agents with human input
"""

import asyncio
import json
from typing import List, Dict, Any
from DebugExerciseAgent import generate_debug_exercises
from DebugEvaluateAgent import evaluate_debug_answers

async def generate_exercises_with_input():
    """Generate debug exercises with human input"""
    print("Generating Debug Exercises")
    print("=" * 60)
    
    # Get input from user
    print("Please provide exercise parameters:")
    topics_input = input("Enter topics (comma-separated, e.g., 'React, Python, Node.js'): ").strip()
    concepts_input = input("Enter concepts (comma-separated, e.g., 'State Management, Memory Leaks'): ").strip()
    num_questions = int(input("Number of questions: ").strip())
    duration_minutes = int(input("Duration in minutes: ").strip())
    difficulty = input("Difficulty level (Easy/Medium/Hard) or press Enter for auto: ").strip()
    
    # Parse inputs
    topics = [topic.strip() for topic in topics_input.split(',') if topic.strip()]
    concepts = [concept.strip() for concept in concepts_input.split(',') if concept.strip()]
    
    # Validate difficulty input
    if difficulty and difficulty.lower() not in ['easy', 'medium', 'hard']:
        print(f"Invalid difficulty '{difficulty}'. Using auto-determination based on time.")
        difficulty = None
    
    result = await generate_debug_exercises(topics, concepts, num_questions, duration_minutes, difficulty)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return None
    
    print("Exercises generated successfully!")
    print(f"Generated {num_questions} exercises for {duration_minutes} minutes")
    print(f"Topics: {', '.join(topics)}")
    print(f"Concepts: {', '.join(concepts)}")
    print(f"Difficulty: {difficulty if difficulty else 'Auto-determined'}")
    
    return result

async def evaluate_answers_with_input(exercises_data: Dict[str, Any]):
    """Evaluate answers with human input"""
    print("\nEvaluating Answers")
    print("=" * 60)
    
    # Extract exercises from the data structure
    exercises = exercises_data.get("exercises", [])
    
    # Get user answers
    print(f"Please provide answers for {len(exercises)} exercises:")
    user_answers = {}
    for i, exercise in enumerate(exercises, 1):
        exercise_id = exercise.get("id", f"exercise_{i}")
        print(f"\nExercise {i}: {exercise.get('title', 'Unknown')}")
        answer = input(f"Enter your solution for exercise {i}: ").strip()
        user_answers[exercise_id] = answer
    
    result = await evaluate_debug_answers(exercises_data, user_answers)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return None
    
    print("Answers evaluated successfully!")
    print(f"Overall Score: {result['overall_score']}")
    print(f"Overall Grade: {result['overall_grade']}")
    
    return result

async def run_workflow():
    """Run the complete workflow with human input"""
    print("Running Debug Exercise Workflow")
    print("=" * 60)
    
    # Step 1: Generate exercises
    exercises_result = await generate_exercises_with_input()
    if not exercises_result:
        return
    
    # Step 2: Check if exercises exist
    exercises = exercises_result.get("exercises", [])
    if not exercises:
        print("No exercises found in result")
        return
    
    # Step 3: Evaluate answers (pass the full exercises_data structure)
    evaluation_result = await evaluate_answers_with_input(exercises_result)
    if not evaluation_result:
        return
    
    # Step 4: Display summary
    print("\nWorkflow Summary")
    print("=" * 60)
    print(f"Generated: {len(exercises)} exercises")
    print(f"Overall Score: {evaluation_result['overall_score']}")
    print(f"Overall Grade: {evaluation_result['overall_grade']}")
    print(f"Correct Solutions: {evaluation_result['summary']['correct_solutions']}")
    print(f"Incorrect Solutions: {evaluation_result['summary']['incorrect_solutions']}")
    
    # Save results to files
    with open("generated_exercises.json", "w") as f:
        json.dump(exercises_result, f, indent=2)
    
    with open("evaluation_results.json", "w") as f:
        json.dump(evaluation_result, f, indent=2)
    
    print("Results saved to files:")
    print("   - generated_exercises.json")
    print("   - evaluation_results.json")

def run_sync():
    """Synchronous wrapper for the workflow"""
    asyncio.run(run_workflow())

if __name__ == "__main__":
    run_sync()
