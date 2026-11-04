from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.passport import AgentRun
from backend.app.schemas.passport import AgentRunResponse

router = APIRouter(prefix="/agent", tags=["Agent Control Center"])

@router.get("/runs", response_model=List[AgentRunResponse])
def get_agent_runs(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit).all()

@router.get("/stats")
def get_agent_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    runs = db.query(AgentRun).all()
    total_runs = len(runs)
    avg_latency = sum(r.execution_time_ms for r in runs) // max(1, total_runs)
    
    agent_counts = {}
    for r in runs:
        agent_counts[r.agent_name] = agent_counts.get(r.agent_name, 0) + 1

    return {
        "total_executions": total_runs,
        "average_latency_ms": avg_latency,
        "active_specialist_agents": [
            {"name": "Orchestrator Agent", "status": "ONLINE", "role": "Pipeline Routing & Coordination"},
            {"name": "Brand Voice Agent", "status": "ONLINE", "role": "Tone & Style Heuristics"},
            {"name": "Terminology Agent", "status": "ONLINE", "role": "Lexicon & Nomenclature Verification"},
            {"name": "ClaimDNA Agent", "status": "ONLINE", "role": "Promotional Claim & Price Fact Verification"},
            {"name": "Suggestion Agent", "status": "ONLINE", "role": "Contextual Correction Generation"},
            {"name": "Guideline Gap Agent", "status": "ONLINE", "role": "Uncovered Claim Detection"}
        ],
        "execution_distribution": agent_counts
    }
