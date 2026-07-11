from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import InteractionCreate, InteractionUpdate, InteractionOut

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


def _to_out(interaction: models.Interaction) -> InteractionOut:
    return InteractionOut(
        id=interaction.id,
        hcp_id=interaction.hcp_id,
        hcp_name=interaction.hcp.name if interaction.hcp else None,
        interaction_type=interaction.interaction_type,
        interaction_date=interaction.interaction_date,
        topics_discussed=interaction.topics_discussed,
        outcomes=interaction.outcomes,
        follow_up_actions=interaction.follow_up_actions,
        sentiment=interaction.sentiment,
        sentiment_confidence=interaction.sentiment_confidence or 0.0,
        source=interaction.source,
        materials_shared=[
            {"id": m.id, "name": m.name, "category": m.category, "product": m.product}
            for m in interaction.materials_shared
        ],
        samples=[
            {"sample_id": s.sample_id, "name": s.sample.name, "quantity": s.quantity}
            for s in interaction.samples
        ],
        created_at=interaction.created_at,
        updated_at=interaction.updated_at,
    )


@router.get("", response_model=List[InteractionOut])
def list_interactions(hcp_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Interaction)
    if hcp_id:
        q = q.filter(models.Interaction.hcp_id == hcp_id)
    rows = q.order_by(models.Interaction.interaction_date.desc()).limit(100).all()
    return [_to_out(r) for r in rows]


@router.get("/{interaction_id}", response_model=InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    row = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return _to_out(row)


@router.post("", response_model=InteractionOut, status_code=201)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    """Handles the structured-form 'Log' button submit."""
    hcp = db.query(models.HCP).filter(models.HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")

    interaction = models.Interaction(
        hcp_id=payload.hcp_id,
        interaction_type=payload.interaction_type,
        interaction_date=payload.interaction_date,
        topics_discussed=payload.topics_discussed,
        outcomes=payload.outcomes,
        follow_up_actions=payload.follow_up_actions,
        sentiment=payload.sentiment or "neutral",
        source="form",
    )

    if payload.attendee_ids:
        interaction.attendees = (
            db.query(models.HCP).filter(models.HCP.id.in_(payload.attendee_ids)).all()
        )
    if payload.material_ids:
        interaction.materials_shared = (
            db.query(models.Material).filter(models.Material.id.in_(payload.material_ids)).all()
        )

    db.add(interaction)
    db.flush()

    for s in payload.samples:
        db.add(models.SampleDistribution(
            interaction_id=interaction.id, sample_id=s.sample_id, quantity=s.quantity
        ))

    db.commit()
    db.refresh(interaction)
    return _to_out(interaction)


@router.patch("/{interaction_id}", response_model=InteractionOut)
def edit_interaction_endpoint(
    interaction_id: str, payload: InteractionUpdate, db: Session = Depends(get_db)
):
    """Handles edits made directly in the form (as opposed to via chat,
    which goes through the edit_interaction LangGraph tool)."""
    interaction = db.query(models.Interaction).filter(
        models.Interaction.id == interaction_id
    ).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    data = payload.model_dump(exclude_unset=True)

    for field in ["interaction_type", "interaction_date", "topics_discussed",
                  "outcomes", "follow_up_actions", "sentiment", "hcp_id"]:
        if field in data and data[field] is not None:
            setattr(interaction, field, data[field])

    if "attendee_ids" in data and data["attendee_ids"] is not None:
        interaction.attendees = (
            db.query(models.HCP).filter(models.HCP.id.in_(data["attendee_ids"])).all()
        )
    if "material_ids" in data and data["material_ids"] is not None:
        interaction.materials_shared = (
            db.query(models.Material).filter(models.Material.id.in_(data["material_ids"])).all()
        )
    if "samples" in data and data["samples"] is not None:
        db.query(models.SampleDistribution).filter(
            models.SampleDistribution.interaction_id == interaction_id
        ).delete()
        for s in data["samples"]:
            db.add(models.SampleDistribution(
                interaction_id=interaction_id, sample_id=s["sample_id"], quantity=s.get("quantity", 1)
            ))

    interaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(interaction)
    return _to_out(interaction)


@router.delete("/{interaction_id}", status_code=204)
def delete_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(
        models.Interaction.id == interaction_id
    ).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()
    return None