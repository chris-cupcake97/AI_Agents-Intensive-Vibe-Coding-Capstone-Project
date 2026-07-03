"""FastAPI app for the ScholarProof backend."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import services
from .schemas import (
    DraftEmailRequest,
    ProfileRequest,
    SaveResultRequest,
    SearchScholarshipsRequest,
    VerifyScholarshipRequest,
    model_to_dict,
)


app = FastAPI(
    title="ScholarProof API",
    version="0.1.0",
    description="Fixture-mode backend API for scholarship source and eligibility verification.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _call(service_fn: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return service_fn(*args, **kwargs)
    except services.ApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.get("/health")
def health() -> dict[str, Any]:
    return services.health()


@app.post("/api/profile")
def create_profile(request: ProfileRequest) -> dict[str, Any]:
    return _call(services.create_profile, model_to_dict(request))


@app.get("/api/profile/{profile_id}")
def get_profile(profile_id: str) -> dict[str, Any]:
    return _call(services.get_profile, profile_id)


@app.post("/api/search-scholarships")
def search_scholarships(request: SearchScholarshipsRequest) -> dict[str, Any]:
    return _call(services.search_scholarships, model_to_dict(request))


@app.post("/api/verify-scholarship")
def verify_scholarship(request: VerifyScholarshipRequest) -> dict[str, Any]:
    return _call(services.verify_scholarship, model_to_dict(request))


@app.get("/api/evidence/{verification_id}")
def get_evidence(verification_id: str) -> dict[str, Any]:
    return _call(services.get_evidence, verification_id)


@app.post("/api/draft-email")
def draft_email(request: DraftEmailRequest) -> dict[str, Any]:
    return _call(services.draft_email, model_to_dict(request))


@app.post("/api/save-result")
def save_result(request: SaveResultRequest) -> dict[str, Any]:
    return _call(services.save_result, model_to_dict(request))


@app.get("/api/saved-results/{profile_id}")
def get_saved_results(profile_id: str) -> dict[str, Any]:
    return _call(services.get_saved_results, profile_id)


@app.get("/api/audit/{verification_id}")
def get_audit(verification_id: str) -> dict[str, Any]:
    return _call(services.get_audit, verification_id)
