import os
import logging
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from ..Agents.EpicAgent import EpicGenerationSystem
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

logger = logging.getLogger(__name__)
# print("agent_chat.py loaded")  # Add this line for confirmation
router = APIRouter()


@router.websocket("/ws/epic-review")
async def epic_review(websocket: WebSocket):
    await websocket.accept()
    try:
        # Step 1: Receive POC details from frontend
        data = await websocket.receive_json()
        poc_details = data.get("poc_details")
        if not poc_details:
            await websocket.send_json({"type": "error", "content": "Missing 'poc_details' in initial message"})
            await websocket.close()
            return

        # Step 2: Setup EpicGenerationSystem
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            # azure_endpoint = AZURE_OPENAI_ENDPOINT,
            # api_key = AZURE_OPENAI_API_KEY
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        epic_system = EpicGenerationSystem(model_client)

        # Step 3: Generate initial epics and feedback/refinement
        epics = await epic_system.generate_initial_epics(poc_details)
        feedback = await epic_system.get_feedback(epics)
        refined_epics = await epic_system.refine_epics(epics, feedback)

        # Step 4: Interactive human review loop
        max_iterations = 3
        iteration = 0
        while iteration < max_iterations:
            # Send epics to frontend for review
            await websocket.send_json({
                "type": "review",
                "content": refined_epics,
                "iteration": iteration + 1
            })
            # Wait for user decision
            user_decision_msg = await websocket.receive_json()
            user_decision = user_decision_msg.get("decision", "").strip()
            user_feedback = user_decision_msg.get("feedback", "")

            if user_decision == "APPROVE":
                await websocket.send_json({
                    "type": "final",
                    "content": refined_epics
                })
                await model_client.close()
                await websocket.close()
                return
            elif user_decision == "REJECT":
                epics = await epic_system.generate_initial_epics(poc_details)
                feedback = await epic_system.get_feedback(epics)
                refined_epics = await epic_system.refine_epics(epics, feedback)
                iteration = 0
            elif user_decision == "REFINE":
                additional_feedback = await epic_system.get_feedback(refined_epics)
                refined_epics = await epic_system.refine_epics(refined_epics, additional_feedback)
            elif user_decision.startswith("FEEDBACK"):
                specific_feedback = user_feedback or user_decision.replace("FEEDBACK:", "").strip()
                refined_epics = await epic_system.refine_epics(refined_epics, specific_feedback)
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid decision. Please send APPROVE, REJECT, REFINE, or FEEDBACK."
                })
                continue
            iteration += 1

        # If max iterations reached, send current version
        await websocket.send_json({
            "type": "final",
            "content": refined_epics
        })
        await model_client.close()
        await websocket.close()

    except WebSocketDisconnect:
        logger.info("Client disconnected during epic review")
    except Exception as e:
        logger.error(f"Error in /ws/epic-review: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
        await websocket.close()
