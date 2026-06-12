"""Smoke tests generated from the blueprint contract."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SMOKE = [
  {
    "method": "post",
    "path": "/api/score",
    "json": {
      "run_id": "r1",
      "prompt": "Refund policy?",
      "answer": "Refunds are processed within 14 days via the original payment method.",
      "reference_keywords": [
        "14 days",
        "refund"
      ],
      "forbidden_keywords": [
        "ssn"
      ]
    }
  },
  {
    "method": "get",
    "path": "/api/report/r1"
  }
]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_smoke_endpoints():
    for case in SMOKE:
        fn = getattr(client, case["method"])
        kwargs = {"json": case["json"]} if "json" in case else {}
        r = fn(case["path"], **kwargs)
        assert r.status_code < 500, f"{case['path']} -> {r.status_code}: {r.text}"
