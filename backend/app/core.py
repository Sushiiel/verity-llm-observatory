"""LLM evaluation observatory core: regression harness with grounding / refusal / verbosity metrics."""
import re, statistics, time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class EvalCase(BaseModel):
    run_id: str
    prompt: str
    answer: str
    reference_keywords: list[str] = []     # facts the answer SHOULD contain
    forbidden_keywords: list[str] = []     # facts/PII the answer must NOT contain

RUNS: dict[str, list[dict]] = {}
REFUSAL = re.compile(r"\b(i can.?t|i cannot|unable to|as an ai)\b", re.IGNORECASE)

@router.post("/score")
def score(c: EvalCase):
    ans = c.answer.lower()
    grounded = sum(1 for k in c.reference_keywords if k.lower() in ans)
    grounding = grounded / len(c.reference_keywords) if c.reference_keywords else None
    leaks = [k for k in c.forbidden_keywords if k.lower() in ans]
    metrics = {
        "grounding": round(grounding, 3) if grounding is not None else None,
        "leakage": len(leaks),
        "refusal": bool(REFUSAL.search(c.answer)),
        "verbosity_tokens": len(c.answer.split()),
        "ts": time.time(),
    }
    RUNS.setdefault(c.run_id, []).append({"prompt": c.prompt[:120], **metrics, "leaked": leaks})
    return metrics

@router.get("/report/{run_id}")
def report(run_id: str):
    cases = RUNS.get(run_id)
    if not cases:
        raise HTTPException(404, "unknown run")
    g = [c["grounding"] for c in cases if c["grounding"] is not None]
    return {
        "run_id": run_id,
        "cases": len(cases),
        "avg_grounding": round(statistics.mean(g), 3) if g else None,
        "refusal_rate": round(sum(c["refusal"] for c in cases) / len(cases), 3),
        "leakage_incidents": sum(c["leakage"] for c in cases),
        "p50_verbosity": statistics.median(c["verbosity_tokens"] for c in cases),
        "worst_cases": sorted(cases, key=lambda c: (c["grounding"] or 1))[:3],
    }

@router.get("/runs")
def runs():
    return {rid: len(cs) for rid, cs in RUNS.items()}
