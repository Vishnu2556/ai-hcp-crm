import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, Text, ForeignKey, Enum, Table, Integer, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class InteractionTypeEnum(str, enum.Enum):
    meeting = "Meeting"
    call = "Call"
    email = "Email"
    conference = "Conference"
    virtual = "Virtual Meeting"


# Many-to-many: interaction <-> materials shared
interaction_materials = Table(
    "interaction_materials",
    Base.metadata,
    Column("interaction_id", UUID(as_uuid=False), ForeignKey("interactions.id")),
    Column("material_id", UUID(as_uuid=False), ForeignKey("materials.id")),
)

# Many-to-many: interaction <-> attendees (HCPs present, for co-visits)
interaction_attendees = Table(
    "interaction_attendees",
    Base.metadata,
    Column("interaction_id", UUID(as_uuid=False), ForeignKey("interactions.id")),
    Column("hcp_id", UUID(as_uuid=False), ForeignKey("hcps.id")),
)


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255))
    institution = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    tier = Column(String(50))  # e.g. KOL, high-value, standard
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)      # e.g. "OncoBoost Phase III PDF"
    category = Column(String(100))                  # brochure / clinical study / leave-behind
    product = Column(String(150))
    url = Column(String(500))


class Sample(Base):
    __tablename__ = "samples"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    lot_number = Column(String(100))
    quantity_available = Column(Integer, default=0)


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    hcp_id = Column(UUID(as_uuid=False), ForeignKey("hcps.id"), nullable=False)
    rep_id = Column(String(100))  # from auth/session, kept loose here

    interaction_type = Column(Enum(InteractionTypeEnum), default=InteractionTypeEnum.meeting)
    interaction_date = Column(DateTime, nullable=False)

    topics_discussed = Column(Text)
    outcomes = Column(Text)
    follow_up_actions = Column(Text)

    sentiment = Column(Enum(SentimentEnum), default=SentimentEnum.neutral)
    sentiment_confidence = Column(Float, default=0.0)

    source = Column(String(20), default="form")  # "form" or "chat"
    raw_note = Column(Text)  # original free-text note if logged via chat

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    materials_shared = relationship("Material", secondary=interaction_materials)
    attendees = relationship("HCP", secondary=interaction_attendees)
    samples = relationship("SampleDistribution", back_populates="interaction")


class SampleDistribution(Base):
    """Join table with quantity, since samples need a count per interaction."""
    __tablename__ = "sample_distributions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    interaction_id = Column(UUID(as_uuid=False), ForeignKey("interactions.id"))
    sample_id = Column(UUID(as_uuid=False), ForeignKey("samples.id"))
    quantity = Column(Integer, default=1)

    interaction = relationship("Interaction", back_populates="samples")
    sample = relationship("Sample")