from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api import events as events_api
from app.api import recommendations as recommendations_api
from app.clients.spacecatalog import SpaceCatalogError
from app.main import app
from app.models.event import AstronomicalEvent
from app.models.responses import (
    EventFactsResponse,
    RecommendationResponse,
)
from app.services.recommendation_service import RecommendationError


# ============================================================
# Test Client and Sample Data
# ============================================================

client = TestClient(app)


@pytest.fixture
def sample_event():
    return {
        "id": "shower-perseids-2026-08-13",
        "title": "Perseids at maximum",
        "kind": "shower",
        "time": "2026-08-13T02:09:26.918Z",
        "description": "Annual meteor shower.",
        "circumstances": {"zhr": 100},
    }


@pytest.fixture
def recommendation_payload(sample_event):
    return {
        "event": sample_event,
        "preferences": {
            "feature": "facts",
            "explanation_level": "simple",
            "interest": "science",
        },
    }


# ============================================================
# Health Endpoint
# ============================================================

def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "SkyWatch AI",
    }


# ============================================================
# Events Endpoint
# ============================================================

def test_events_success(monkeypatch, sample_event):
    def fake_get_events(self, from_date, to_date):
        assert from_date == date(2026, 8, 1)
        assert to_date == date(2026, 8, 31)

        return [AstronomicalEvent.model_validate(sample_event)]

    monkeypatch.setattr(
        events_api.SpaceCatalogClient,
        "get_events",
        fake_get_events,
    )

    response = client.get(
        "/api/events",
        params={
            "from_date": "2026-08-01",
            "to_date": "2026-08-31",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["title"] == "Perseids at maximum"


def test_events_empty(monkeypatch):
    def fake_get_events(self, from_date, to_date):
        return []

    monkeypatch.setattr(
        events_api.SpaceCatalogClient,
        "get_events",
        fake_get_events,
    )

    response = client.get(
        "/api/events",
        params={
            "from_date": "2026-08-01",
            "to_date": "2026-08-31",
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["events"] == []


def test_events_invalid_date_range():
    response = client.get(
        "/api/events",
        params={
            "from_date": "2026-12-31",
            "to_date": "2026-01-01",
        },
    )

    assert response.status_code == 400


def test_events_range_too_long():
    response = client.get(
        "/api/events",
        params={
            "from_date": "2026-01-01",
            "to_date": "2027-12-31",
        },
    )

    assert response.status_code == 400


def test_events_invalid_date_format():
    response = client.get(
        "/api/events",
        params={
            "from_date": "invalid-date",
        },
    )

    assert response.status_code == 422


def test_events_provider_failure(monkeypatch):
    def fake_get_events(self, from_date, to_date):
        raise SpaceCatalogError("Provider unavailable.")

    monkeypatch.setattr(
        events_api.SpaceCatalogClient,
        "get_events",
        fake_get_events,
    )

    response = client.get(
        "/api/events",
        params={
            "from_date": "2026-08-01",
            "to_date": "2026-08-31",
        },
    )

    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"].lower()


# ============================================================
# Recommendation Endpoint
# ============================================================

def test_recommendation_success(
    monkeypatch,
    recommendation_payload,
):
    def fake_generate(self, request):
        assert request.preferences.feature == "facts"

        return RecommendationResponse(
            feature="facts",
            result=EventFactsResponse(
                event_name=request.event.title,
                explanation="The Perseids are a meteor shower.",
                facts=[
                    {
                        "title": "Parent comet",
                        "description": "Comet Swift-Tuttle.",
                    }
                ],
            ),
        )

    monkeypatch.setattr(
        recommendations_api.RecommendationService,
        "generate",
        fake_generate,
    )

    response = client.post(
        "/api/recommendations",
        json=recommendation_payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["feature"] == "facts"
    assert data["result"]["event_name"] == "Perseids at maximum"
    assert len(data["result"]["facts"]) == 1


def test_recommendation_invalid_feature(
    recommendation_payload,
):
    recommendation_payload["preferences"]["feature"] = "unrelated"

    response = client.post(
        "/api/recommendations",
        json=recommendation_payload,
    )

    assert response.status_code == 422


def test_recommendation_missing_event():
    response = client.post(
        "/api/recommendations",
        json={
            "preferences": {
                "feature": "facts",
                "explanation_level": "simple",
                "interest": "science",
            }
        },
    )

    assert response.status_code == 422


def test_recommendation_invalid_preferences(
    sample_event,
):
    response = client.post(
        "/api/recommendations",
        json={
            "event": sample_event,
            "preferences": {
                "feature": "locations",
                "origin": "Ljubljana",
                "max_distance_km": 1000,
                "transport": "car",
                "priority": "dark_sky",
            },
        },
    )

    assert response.status_code == 422


def test_recommendation_provider_failure(
    monkeypatch,
    recommendation_payload,
):
    def fake_generate(self, request):
        raise RecommendationError("Provider failure.")

    monkeypatch.setattr(
        recommendations_api.RecommendationService,
        "generate",
        fake_generate,
    )

    response = client.post(
        "/api/recommendations",
        json=recommendation_payload,
    )

    assert response.status_code == 502

    assert response.json()["detail"] == (
        "AI recommendation service is currently unavailable."
    )
