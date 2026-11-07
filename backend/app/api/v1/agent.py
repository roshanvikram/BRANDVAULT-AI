from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.passport import AgentRun
from backend.app.schemas.passport import AgentRunResponse

from backend.app.models.user import User
from backend.app.api.deps import get_current_user, resolve_org, ensure_same_org

router = APIRouter(prefix="/agent", tags=["Agent Control Center"])

@router.get("/runs", response_model=List[AgentRunResponse])
def get_agent_runs(limit: int = 50, db: Session = Depends(get_db),
                   current: User = Depends(get_current_user)):
    # Runs recorded before Phase 1a have no org and are not shown to any tenant.
    return db.query(AgentRun).filter(AgentRun.org_id == current.org_id).order_by(AgentRun.created_at.desc()).limit(limit).all()

@router.get("/stats")
def get_agent_stats(db: Session = Depends(get_db),
                    current: User = Depends(get_current_user)) -> Dict[str, Any]:
    runs = db.query(AgentRun).filter(AgentRun.org_id == current.org_id).all()
    total_runs = len(runs)

    # Agent steps run sub-millisecond, so integer-ms averaging rounded to 0.
    # Use microsecond-precision timing where available for a truthful figure.
    us_values = [r.execution_time_us for r in runs if r.execution_time_us]
    if us_values:
        avg_us = sum(us_values) / len(us_values)
        average_latency_ms = round(avg_us / 1000, 3)
        average_latency_us = round(avg_us, 1)
    else:
        average_latency_ms = 0.0
        average_latency_us = 0.0

    agent_counts = {}
    for r in runs:
        agent_counts[r.agent_name] = agent_counts.get(r.agent_name, 0) + 1

    return {
        "total_executions": total_runs,
        "average_latency_ms": average_latency_ms,
        "average_latency_us": average_latency_us,
        "timed_executions": len(us_values),
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

