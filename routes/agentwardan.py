from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import Depends
from pydantic import BaseModel
from agent.graph import agentwardan_chat
from database.db import Session
from models.models import Student
from utils.auth import require_role
from models.models import UserRole
from typing import Any, Dict, List
import json


router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentQuery(BaseModel):
    query: str
    session_id: str | None = None


def _envelope_from_answer(answer: Any) -> Dict[str, Any]:
    """Builds a {summary, data} envelope from various answer forms.
    - If answer is already an object with summary/data, pass through.
    - If answer is JSON string, parse and analyze.
    - If answer is a list/dict, compute a concise summary and set as data.
    - Otherwise, treat as plain text summary with empty data.
    """
    try:
        # If already dict with summary/data
        if isinstance(answer, dict) and "summary" in answer and "data" in answer:
            return {"summary": str(answer.get("summary", "")), "data": answer.get("data") or []}

        # If string, try to parse JSON
        if isinstance(answer, str):
            try:
                parsed = json.loads(answer)
                answer = parsed
            except Exception:
                # Non-JSON string, return as summary
                return {"summary": answer, "data": []}

        # If list, compute count summary
        if isinstance(answer, list):
            count = len(answer)
            preview = answer[:10]
            return {"summary": f"Found {count} record(s). Showing {len(preview)}.", "data": preview}

        # If dict, try to recognize common shapes
        if isinstance(answer, dict):
            # If it has an array payload
            for key, value in answer.items():
                if isinstance(value, list):
                    count = len(value)
                    preview = value[:10]
                    return {"summary": f"{key}: {count} item(s). Showing {len(preview)}.", "data": preview}
            # Otherwise return the dict as a single datum
            return {"summary": "1 record.", "data": [answer]}
    except Exception:
        pass
    # Fallback
    return {"summary": str(answer), "data": []}


@router.post("/query")
async def agent_query(payload: AgentQuery, user=Depends(require_role([UserRole.admin, UserRole.agent]))):
    """Single-shot agent query endpoint (REST)."""
    q = (payload.query or "").strip().lower()

    # Lightweight fallbacks for common intents to ensure responsiveness
    if q and any(k in q for k in ["show students", "students list", "list students", "show me students"]):
        db = Session()
        try:
            students = db.query(Student).all()
            data = [
                {
                    "id": s.id,
                    "name": s.name,
                    "room_no": (s.room.room_no if getattr(s, "room", None) else "Unassigned"),
                }
                for s in students
            ]
            count = len(data)
            summary = f"There are {count} students. Showing {min(10, count)}."
            return {"summary": summary, "data": data[:10]}
        finally:
            db.close()

    try:
        answer = await agentwardan_chat(payload.query, session_id=payload.session_id or "default")
        envelope = _envelope_from_answer(answer)
        return envelope
    except Exception as e:
        return {"summary": f"Agent error: {e}", "data": []}


@router.websocket("/ws/agent")
async def agent_ws(ws: WebSocket):
    """Simple WS that accepts a JSON: {"query": "..."} and returns {"answer": "..."}.
    For now we return once; can be extended to streaming tokens.
    """
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            user_query = data.get("query", "")
            session_id = data.get("session_id") or "default"
            if not user_query:
                await ws.send_json({"summary": "query is required", "data": []})
                continue
            answer = await agentwardan_chat(user_query, session_id=session_id)
            envelope = _envelope_from_answer(answer)
            await ws.send_json(envelope)
    except WebSocketDisconnect:
        pass
