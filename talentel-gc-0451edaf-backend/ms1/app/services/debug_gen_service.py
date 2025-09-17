from ..models.models import DebugExercise, DebugResult
from ..config.database import get_db

def save_debug_results(path_id, user_id, results):
    db = None
    try:
        db = next(get_db())  # Get the session from the generator

        debug_exercise = db.query(DebugExercise).filter(DebugExercise.path_id == path_id).first()
        if not debug_exercise:
            raise Exception(f"No debug exercise found for path_id {path_id}")

        overall_eval = results.get("overall_evaluation")
        print(f"overall_evaluation: {overall_eval}")
        if isinstance(overall_eval, dict):
            overall_score = overall_eval.get("overall_score")
        else:
            overall_score = getattr(overall_eval, "overall_score", None)
        print(f"overall_score: {overall_score}")

        debug_result = DebugResult(
            user_id=user_id,
            score=overall_score,
            feedback_data=results,
            debug_id=debug_exercise.id
        )

        db.add(debug_result)
        db.commit()
        db.refresh(debug_result)
        print(f"Saved debug results: {debug_result.result_id}")
        return debug_result

    except Exception as ex:
        print(f"Error saving debug results: {ex}")
        return None

    finally:
        if db:
            db.close()
