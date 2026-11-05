from typing import Literal

from pydantic import BaseModel, Field, model_validator


# ============================================================
# Common Response Models
# ============================================================

class AIResponseBase(BaseModel):
    """Common fields for all AI-generated responses."""

    event_name: str
    warning: str | None = None


# ============================================================
# Observation Locations
# ============================================================

class ObservationLocation(BaseModel):
    """A suggested location for observing an event."""

    name: str
    reason: str


class LocationRecommendationResponse(AIResponseBase):
    """AI response containing suggested observation locations."""

    observable: bool
    locations: list[ObservationLocation] = Field(max_length=3)
    general_advice: str

    @model_validator(mode="after")
    def validate_observability(self):
        """Ensure locations are consistent with observability."""

        if not self.observable and self.locations:
            raise ValueError(
                "Unobservable events must not have suggested locations."
            )

        if self.observable and not self.locations:
            raise ValueError(
                "Observable events must have at least one location."
            )

        return self


# ============================================================
# Equipment Recommendations
# ============================================================

class EquipmentItem(BaseModel):
    """A recommended piece of observation equipment."""

    name: str
    reason: str


class EquipmentRecommendationResponse(AIResponseBase):
    """AI response containing equipment recommendations."""

    equipment: list[EquipmentItem] = Field(min_length=1)
    general_advice: str


# ============================================================
# Observation Plans
# ============================================================

class ObservationStep(BaseModel):
    """A step in an astronomical observation plan."""

    step: int = Field(ge=1)
    title: str
    description: str


class ObservationPlanResponse(AIResponseBase):
    """AI response containing an observation plan."""

    steps: list[ObservationStep] = Field(min_length=1)
    general_advice: str


# ============================================================
# Astronomical Facts
# ============================================================

class InterestingFact(BaseModel):
    """An interesting fact about an astronomical event."""

    title: str
    description: str


class EventFactsResponse(AIResponseBase):
    """AI response containing an explanation and interesting facts."""

    explanation: str
    facts: list[InterestingFact] = Field(min_length=1)


# ============================================================
# API Response
# ============================================================

AIResponse = (
    LocationRecommendationResponse
    | EquipmentRecommendationResponse
    | ObservationPlanResponse
    | EventFactsResponse
)


class RecommendationResponse(BaseModel):
    """Structured recommendation returned to the frontend."""

    feature: Literal["locations", "equipment", "plan", "facts"]
    result: AIResponse
