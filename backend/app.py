from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import interaction, ai

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HCP CRM - Log Interaction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interaction.router)
app.include_router(ai.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}