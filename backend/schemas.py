from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MaterialOut(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    product: Optional[str] = None

    class Config:
        from_attributes = True


class SampleDistributionIn(BaseModel):
    sample_id: str
    quantity: int = 1


class SampleDistributionOut(BaseModel):
    sample_id: str
    name: str
    quantity: int

    class Config:
        from_attributes = True


class InteractionBase(BaseModel):
    hcp_id: str
    interaction_type: str = "Meeting"
    interaction_date: datetime
    attendee_ids: List[str] = Field(default_factory=list)
    topics_discussed: Optional[str] = None
    material_ids: List[str] = Field(default_factory=list)
    samples: List[SampleDistributionIn] = Field(default_factory=list)
    sentiment: Optional[str] = "neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionCreate(InteractionBase):
    """Used by the structured form submit."""
    source: str = "form"


class InteractionUpdate(BaseModel):
    """All fields optional - partial update for Edit Interaction."""
    hcp_id: Optional[str] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[datetime] = None
    attendee_ids: Optional[List[str]] = None
    topics_discussed: Optional[str] = None
    material_ids: Optional[List[str]] = None
    samples: Optional[List[SampleDistributionIn]] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionOut(BaseModel):
    id: str
    hcp_id: str
    hcp_name: Optional[str] = None
    interaction_type: str
    interaction_date: datetime
    topics_discussed: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    sentiment: str
    sentiment_confidence: float = 0.0
    source: str
    materials_shared: List[MaterialOut] = Field(default_factory=list)
    samples: List[SampleDistributionOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageIn(BaseModel):
    session_id: str
    message: str
    rep_id: Optional[str] = "rep_demo"


class ChatMessageOut(BaseModel):
    session_id: str
    reply: str
    # populated when the agent actually created/edited an interaction,
    # so the frontend form/state can sync without a full refetch
    interaction: Optional[InteractionOut] = None
    suggested_follow_ups: List[str] = Field(default_factory=list)
    pending_confirmation: bool = False