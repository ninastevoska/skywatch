import pytest
from pydantic import ValidationError

from app.models.event import AstronomicalEvent
from app.models.requests import (
    EquipmentPreferences,
    FactsPreferences,
    LocationPreferences,
    PlanPreferences,
    RecommendationRequest,
)
from app.models.responses import (
    EventFactsResponse,
    LocationRecommendationResponse,
)


# ============================================================
# Test Data
# ============================================================

@pytest.fixture
def sample_event():
    return {
        "id": "shower-perseids-2026-08-13",
        "title": "Perseids at maximum",
        "kind": "shower",
        "time": "2026-08-13T02:09:26.918Z",
        "description": "Annual meteor shower.",
        "circumstances": {
            "zhr": 100,
        },
    }


# ============================================================
# Astronomical Event Tests
# ============================================================

def test_valid_astronomical_event(sample_event):
    event = AstronomicalEvent.model_validate(sample_event)

    assert event.title == "Perseids at maximum"
    assert event.kind == "shower"
    assert event.circumstances["zhr"] == 100


def test_event_requires_title(sample_event):
    sample_event.pop("title")

    with pytest.raises(ValidationError):
        AstronomicalEvent.model_validate(sample_event)


def test_event_rejects_invalid_time(sample_event):
    sample_event["time"] = "not-a-date"

    with pytest.raises(ValidationError):
        AstronomicalEvent.model_validate(sample_event)


# ============================================================
# User Preferences Tests
# ============================================================

def test_location_preferences():
    preferences = LocationPreferences(
        origin="Ljubljana",
        max_distance_km=50,
        transport="car",
        priority="dark_sky",
    )

    assert preferences.feature == "locations"
    assert preferences.max_distance_km == 50


def test_location_distance_limit():
    with pytest.raises(ValidationError):
        LocationPreferences(
            origin="Ljubljana",
            max_distance_km=1000,
            transport="car",
            priority="dark_sky",
        )


def test_equipment_preferences():
    preferences = EquipmentPreferences(
        experience="beginner",
        available_equipment="binoculars",
        observation_mode="visual",
    )

    assert preferences.feature == "equipment"


def test_plan_preferences():
    preferences = PlanPreferences(
        origin="Ljubljana",
        experience="intermediate",
        duration="1_to_3_hours",
        observation_mode="photography",
    )

    assert preferences.feature == "plan"


def test_facts_preferences():
    preferences = FactsPreferences(
        explanation_level="simple",
        interest="science",
    )

    assert preferences.feature == "facts"


def test_recommendation_request(sample_event):
    request = RecommendationRequest.model_validate({
        "event": sample_event,
        "preferences": {
            "feature": "facts",
            "explanation_level": "simple",
            "interest": "science",
        },
    })

    assert request.event.title == "Perseids at maximum"
    assert isinstance(request.preferences, FactsPreferences)


def test_invalid_feature(sample_event):
    with pytest.raises(ValidationError):
        RecommendationRequest.model_validate({
            "event": sample_event,
            "preferences": {
                "feature": "unrelated",
            },
        })


# ============================================================
# AI Response Tests
# ============================================================

def test_valid_facts_response():
    response = EventFactsResponse.model_validate({
        "event_name": "Perseids at maximum",
        "explanation": "The Perseids are a meteor shower.",
        "facts": [
            {
                "title": "Parent comet",
                "description": "Comet Swift-Tuttle.",
            },
        ],
    })

    assert len(response.facts) == 1


def test_unobservable_event_returns_no_locations():
    response = LocationRecommendationResponse.model_validate({
        "event_name": "New moon",
        "observable": False,
        "locations": [],
        "general_advice": "The new moon is not directly visible.",
    })

    assert response.observable is False
    assert response.locations == []


def test_location_response_max_three_locations():
    locations = [
        {
            "name": f"Location {i}",
            "reason": "Potential observation site.",
        }
        for i in range(4)
    ]

    with pytest.raises(ValidationError):
        LocationRecommendationResponse.model_validate({
            "event_name": "Perseids at maximum",
            "observable": True,
            "locations": locations,
            "general_advice": "Check local conditions.",
        })
