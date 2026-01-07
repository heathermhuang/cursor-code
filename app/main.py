from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .bazi import compute_bazi
from .fortune import VerificationQuestion, build_future_fortune, generate_verification_questions


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"

app = FastAPI(title="AI 算命（八字/五行）", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@dataclass
class Session:
    chart: dict[str, Any]
    questions: list[VerificationQuestion]
    created_at: datetime
    meta: dict[str, Any]


SESSIONS: dict[str, Session] = {}


class ChartRequest(BaseModel):
    birthDate: str = Field(..., description="YYYY-MM-DD")
    birthTime: str = Field(..., description="HH or HH:MM (24h)")
    gender: str = Field(..., description="male/female/other")
    city: str = Field("", description="出生城市（展示用）")


class ChartResponse(BaseModel):
    sessionId: str
    chart: dict[str, Any]
    verificationQuestions: list[dict[str, Any]]


class ResultRequest(BaseModel):
    sessionId: str
    answers: dict[str, bool]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/chart", response_model=ChartResponse)
def api_chart(req: ChartRequest) -> ChartResponse:
    dt = _parse_birth_datetime(req.birthDate, req.birthTime)
    chart = compute_bazi(dt)

    today = date.today()
    questions = generate_verification_questions(chart, today=today)

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = Session(
        chart=chart,
        questions=questions,
        created_at=datetime.utcnow(),
        meta={"gender": req.gender, "city": req.city, "birth": {"date": req.birthDate, "time": req.birthTime}},
    )

    return ChartResponse(
        sessionId=session_id,
        chart={
            **chart,
            "meta": {"gender": req.gender, "city": req.city, "birth": {"date": req.birthDate, "time": req.birthTime}},
        },
        verificationQuestions=[{"id": q.id, "text": q.text} for q in questions],
    )


@app.post("/api/result")
def api_result(req: ResultRequest) -> dict[str, Any]:
    session = SESSIONS.get(req.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found (請重新排盤)")

    reviewed = []
    total = len(session.questions) or 1
    matched = 0
    answered = 0
    for q in session.questions:
        if q.id in req.answers:
            answered += 1
        ans = bool(req.answers.get(q.id, False))
        ok = ans == q.expected_yes
        if ok:
            matched += 1
        reviewed.append(
            {
                "id": q.id,
                "question": q.text,
                "expectedYes": q.expected_yes,
                "yourAnswer": ans,
                "matched": ok,
                "rationale": q.rationale,
            }
        )

    # 若使用者沒有作答完整，降低匹配分數的可信度（但仍會給出運勢）
    completeness = answered / total
    match_score = (matched / total) * (0.6 + 0.4 * completeness)

    future = build_future_fortune(
        chart=session.chart,
        start_year=date.today().year,
        years=5,
        match_score=match_score,
    )

    return {
        "chart": session.chart,
        "pastReview": {
            "total": total,
            "answered": answered,
            "matched": matched,
            "matchScore": round(match_score, 3),
            "items": reviewed,
        },
        "future": future,
    }


def _parse_birth_datetime(birth_date: str, birth_time: str) -> datetime:
    try:
        y, m, d = [int(x) for x in birth_date.split("-")]
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="birthDate 格式需為 YYYY-MM-DD") from e

    t = birth_time.strip()
    try:
        if ":" in t:
            hh, mm = [int(x) for x in t.split(":")[:2]]
        else:
            hh, mm = int(t), 0
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="birthTime 格式需為 HH 或 HH:MM（24 小時制）") from e

    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise HTTPException(status_code=400, detail="birthTime 不合法")

    return datetime(y, m, d, hh, mm, 0)

