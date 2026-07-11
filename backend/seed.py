"""
Run once after the tables exist to populate demo HCPs/materials/samples:
    python seed.py
"""
from database import SessionLocal, Base, engine
import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(models.HCP).count() == 0:
    db.add_all([
        models.HCP(name="Dr. Sharma", specialty="Oncology", institution="Apollo Hospitals"),
        models.HCP(name="Dr. Smith", specialty="Cardiology", institution="City General"),
        models.HCP(name="Dr. Patel", specialty="Endocrinology", institution="Sunrise Clinic"),
    ])

if db.query(models.Material).count() == 0:
    db.add_all([
        models.Material(name="OncoBoost Phase III PDF", category="Clinical Study", product="OncoBoost"),
        models.Material(name="OncoBoost Leave-Behind Brochure", category="Brochure", product="OncoBoost"),
    ])

if db.query(models.Sample).count() == 0:
    db.add_all([
        models.Sample(name="OncoBoost 50mg Sample Box", lot_number="LOT-2201", quantity_available=200),
    ])

db.commit()
print("Seed complete.")