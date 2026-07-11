import json
from datetime import datetime
from typing import List, Optional

from langchain_core.tools import tool
from sqlalchemy import or_

from database import SessionLocal
import models
from services.groq_services import chat_completion, REASONING_MODEL
from langgraph_agent.prompts import EXTRACTION_PROMPT, SENTIMENT_PROMPT, FOLLOW_UP_PROMPT


def _db():
    return SessionLocal()


# ---------------------------------------------------------------------------
# Tool 1: search_hcp - resolve a spoken/typed HCP name to a real record
# ---------------------------------------------------------------------------
@tool
def search_hcp(name_query: str) -> str:
    """Search the HCP directory by (partial) name. Returns a JSON list of
    matching HCPs with id, name, specialty and institution. Always call this
    before log_interaction/edit_interaction if the HCP wasn't already
    resolved to an id, so you never fabricate an HCP id."""
    db = _db()
    try:
        rows = (
            db.query(models.HCP)
            .filter(models.HCP.name.ilike(f"%{name_query}%"))
            .limit(5)
            .all()
        )
        return json.dumps([
            {"id": r.id, "name": r.name, "specialty": r.specialty, "institution": r.institution}
            for r in rows
        ])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 2: search_materials_samples - resolve brochure/sample names
# ---------------------------------------------------------------------------
@tool
def search_materials_samples(query: str) -> str:
    """Search shareable materials (brochures, studies) AND distributable
    samples by (partial) name. Returns JSON: {"materials": [...], "samples": [...]}.
    Use this to resolve names mentioned in a rep's free-text note before
    attaching them to an interaction."""
    db = _db()
    try:
        materials = (
            db.query(models.Material)
            .filter(models.Material.name.ilike(f"%{query}%"))
            .limit(5)
            .all()
        )
        samples = (
            db.query(models.Sample)
            .filter(models.Sample.name.ilike(f"%{query}%"))
            .limit(5)
            .all()
        )
        return json.dumps({
            "materials": [{"id": m.id, "name": m.name, "category": m.category} for m in materials],
            "samples": [{"id": s.id, "name": s.name, "quantity_available": s.quantity_available} for s in samples],
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 3: get_hcp_history - prior interactions, used for context/continuity
# ---------------------------------------------------------------------------
@tool
def get_hcp_history(hcp_id: str, limit: int = 3) -> str:
    """Return the most recent past interactions for an HCP (JSON list), so
    the agent can reference prior context (e.g. 'last time you promised to
    send the Phase III data') when logging or suggesting follow-ups."""
    db = _db()
    try:
        rows = (
            db.query(models.Interaction)
            .filter(models.Interaction.hcp_id == hcp_id)
            .order_by(models.Interaction.interaction_date.desc())
            .limit(limit)
            .all()
        )
        return json.dumps([
            {
                "id": r.id,
                "date": r.interaction_date.isoformat(),
                "topics_discussed": r.topics_discussed,
                "outcomes": r.outcomes,
                "sentiment": r.sentiment.value if r.sentiment else None,
            }
            for r in rows
        ])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 4: log_interaction - THE core "log via chat" tool
# ---------------------------------------------------------------------------
@tool
def log_interaction(
    hcp_id: str,
    raw_note: str,
    interaction_type: Optional[str] = "Meeting",
    material_ids: Optional[List[str]] = None,
    sample_ids: Optional[List[str]] = None,
) -> str:
    """Create a new HCP interaction record from a rep's free-text note.

    Uses the LLM to extract structured fields (topics discussed, outcomes,
    follow-up actions, sentiment) from `raw_note`, then persists a row.
    `hcp_id` MUST come from a prior search_hcp call - never guess it.
    `material_ids`/`sample_ids` should come from search_materials_samples.
    Returns JSON of the created interaction, including a `follow_ups` array.
    """
    material_ids = material_ids or []
    sample_ids = sample_ids or []

    # 1. LLM extraction pass (gemma2-9b-it, low latency, JSON mode)
    extraction_raw = chat_completion(
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(note=raw_note)}],
        response_format="json_object",
        temperature=0.0,
    )
    try:
        extracted = json.loads(extraction_raw)
    except json.JSONDecodeError:
        extracted = {}

    # 2. Dedicated sentiment pass (kept separate so it's auditable/overridable)
    sentiment_raw = chat_completion(
        messages=[{"role": "user", "content": SENTIMENT_PROMPT.format(note=raw_note)}],
        response_format="json_object",
        temperature=0.0,
    )
    try:
        sentiment_data = json.loads(sentiment_raw)
    except json.JSONDecodeError:
        sentiment_data = {"sentiment": "neutral", "confidence": 0.5}

    db = _db()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        interaction = models.Interaction(
            hcp_id=hcp_id,
            interaction_type=extracted.get("interaction_type") or interaction_type or "Meeting",
            interaction_date=datetime.utcnow(),
            topics_discussed=extracted.get("topics_discussed"),
            outcomes=extracted.get("outcomes"),
            follow_up_actions=extracted.get("follow_up_actions"),
            sentiment=sentiment_data.get("sentiment", "neutral"),
            sentiment_confidence=sentiment_data.get("confidence", 0.5),
            source="chat",
            raw_note=raw_note,
        )

        if material_ids:
            interaction.materials_shared = (
                db.query(models.Material).filter(models.Material.id.in_(material_ids)).all()
            )

        db.add(interaction)
        db.flush()  # get interaction.id before adding sample rows

        for sid in sample_ids:
            db.add(models.SampleDistribution(
                interaction_id=interaction.id, sample_id=sid, quantity=1
            ))

        db.commit()
        db.refresh(interaction)

        result = {
            "id": interaction.id,
            "hcp_name": hcp.name,
            "interaction_type": interaction.interaction_type,
            "topics_discussed": interaction.topics_discussed,
            "outcomes": interaction.outcomes,
            "follow_up_actions": interaction.follow_up_actions,
            "sentiment": interaction.sentiment,
            "sentiment_confidence": interaction.sentiment_confidence,
        }
        return json.dumps(result)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 5: edit_interaction - modify a previously logged interaction
# ---------------------------------------------------------------------------
@tool
def edit_interaction(interaction_id: str, updates_json: str) -> str:
    """Edit an existing interaction. `updates_json` is a JSON string that may
    contain any subset of: interaction_type, topics_discussed, outcomes,
    follow_up_actions, sentiment, material_ids (list), sample_ids (list).

    Use this when the rep says things like "actually change the sentiment to
    positive" or "add the OncoBoost brochure to that visit I just logged" or
    "no I met Dr. Sharma on the 21st not the 19th". Always confirm the
    interaction_id refers to the correct visit (e.g. via get_hcp_history)
    before calling this if there's any ambiguity.
    """
    try:
        updates = json.loads(updates_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "updates_json was not valid JSON"})

    db = _db()
    try:
        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id
        ).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        simple_fields = ["interaction_type", "topics_discussed", "outcomes",
                          "follow_up_actions", "sentiment"]
        for field in simple_fields:
            if field in updates and updates[field] is not None:
                setattr(interaction, field, updates[field])

        if "material_ids" in updates:
            interaction.materials_shared = (
                db.query(models.Material)
                .filter(models.Material.id.in_(updates["material_ids"]))
                .all()
            )

        if "sample_ids" in updates:
            db.query(models.SampleDistribution).filter(
                models.SampleDistribution.interaction_id == interaction_id
            ).delete()
            for sid in updates["sample_ids"]:
                db.add(models.SampleDistribution(
                    interaction_id=interaction_id, sample_id=sid, quantity=1
                ))

        interaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "id": interaction.id,
            "interaction_type": interaction.interaction_type,
            "topics_discussed": interaction.topics_discussed,
            "outcomes": interaction.outcomes,
            "follow_up_actions": interaction.follow_up_actions,
            "sentiment": interaction.sentiment,
            "updated_at": interaction.updated_at.isoformat(),
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 6: suggest_follow_ups - proactive next-best-actions
# ---------------------------------------------------------------------------
@tool
def suggest_follow_ups(interaction_summary: str) -> str:
    """Given a short natural-language summary of an interaction (topics,
    outcomes, sentiment), return up to 3 concrete follow-up action strings
    as a JSON array. Uses the larger reasoning model since follow-up quality
    matters more than latency here."""
    raw = chat_completion(
        messages=[{"role": "user", "content": FOLLOW_UP_PROMPT.format(summary=interaction_summary)}],
        model=REASONING_MODEL,
        temperature=0.3,
    )
    try:
        cleaned = raw.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
        suggestions = json.loads(cleaned)
        if isinstance(suggestions, list):
            return json.dumps(suggestions[:3])
    except (json.JSONDecodeError, AttributeError):
        pass
    return json.dumps([])


ALL_TOOLS = [
    search_hcp,
    search_materials_samples,
    get_hcp_history,
    log_interaction,
    edit_interaction,
    suggest_follow_ups,
]