import json

from fastapi import APIRouter, Depends
from langchain_core.messages import ToolMessage
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import ChatMessageIn, ChatMessageOut
from langgraph_agent.graph import agent_graph

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat", response_model=ChatMessageOut)
def chat(payload: ChatMessageIn, db: Session = Depends(get_db)):
    config = {"configurable": {"thread_id": payload.session_id}}
    result = agent_graph.invoke(
        {"messages": [{"role": "user", "content": payload.message}]},
        config=config,
    )
    messages = result["messages"]
    reply = messages[-1].content

    # Inspect tool messages from this turn to see if log_interaction /
    # edit_interaction actually ran, so the frontend form can sync state
    # without re-fetching everything.
    interaction_payload = None
    follow_ups: list[str] = []

    for m in reversed(messages):
        if isinstance(m, ToolMessage):
            try:
                data = json.loads(m.content)
            except (json.JSONDecodeError, TypeError):
                continue
            if m.name == "log_interaction" and "id" in data and interaction_payload is None:
                interaction_payload = data
            if m.name == "edit_interaction" and "id" in data and interaction_payload is None:
                interaction_payload = data
            if m.name == "suggest_follow_ups" and isinstance(data, list):
                follow_ups = data

    interaction_out = None
    if interaction_payload:
        row = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_payload["id"]
        ).first()
        if row:
            interaction_out = {
                "id": row.id,
                "hcp_id": row.hcp_id,
                "hcp_name": row.hcp.name if row.hcp else None,
                "interaction_type": row.interaction_type,
                "interaction_date": row.interaction_date,
                "topics_discussed": row.topics_discussed,
                "outcomes": row.outcomes,
                "follow_up_actions": row.follow_up_actions,
                "sentiment": row.sentiment,
                "sentiment_confidence": row.sentiment_confidence or 0.0,
                "source": row.source,
                "materials_shared": [
                    {"id": mm.id, "name": mm.name, "category": mm.category, "product": mm.product}
                    for mm in row.materials_shared
                ],
                "samples": [
                    {"sample_id": s.sample_id, "name": s.sample.name, "quantity": s.quantity}
                    for s in row.samples
                ],
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }

    return ChatMessageOut(
        session_id=payload.session_id,
        reply=reply,
        interaction=interaction_out,
        suggested_follow_ups=follow_ups,
        pending_confirmation=False,
    )