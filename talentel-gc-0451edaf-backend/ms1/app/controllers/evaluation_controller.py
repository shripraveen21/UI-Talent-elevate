import asyncio
from ..utils.evaluation_scheduler import evaluate_unevaluated_handson_assignments, evaluate_unevaluated_debug_assignments
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

# Add another endpoint here above the /evaluate/all

@router.get("/evaluate/all")
async def evaluate_all():
    try:
        asyncio.create_task(evaluate_unevaluated_handson_assignments())
        asyncio.create_task(evaluate_unevaluated_debug_assignments())
        return {
            "success": True,
            "details": "Evaluation Started",
        }
    except Exception as e:
        print(e)
        raise HTTPException(500, detail="Something went wrong")
