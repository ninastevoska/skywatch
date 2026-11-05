from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.models.event import AstronomicalEvent


class AIFeature(str, Enum):
    LOCATIONS = "locations"
    EQUIPMENT = "equipment"
    PLAN = "plan"
    FACTS = "facts"


class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"


class ObservationMode(str, Enum):
    VISUAL = "visual"
    PHOTOGRAPHY = "photography"


class TransportMode(str, Enum):
    CAR = "car"
    BICYCLE = "bicycle"
    WALKING = "walking"


class LocationPreferences(BaseModel):
    feature: Literal["locations"] = "locations"

    origin: str = Field(min_length=2, max_length=150)
    max_distance_km: int = Field(ge=1, le=500)
    transport: TransportMode
    priority: Literal[
        "dark_sky",
        "easy_access",
        "open_horizon",
    ]


class EquipmentPreferences(BaseModel):
    feature: Literal["equipment"] = "equipment"

    experience: ExperienceLevel
    available_equipment: Literal[
        "none",
        "binoculars",
        "telescope",
    ]
    observation_mode: ObservationMode


class PlanPreferences(BaseModel):
    feature: Literal["plan"] = "plan"

    origin: str = Field(min_length=2, max_length=150)
    experience: ExperienceLevel
    duration: Literal[
        "under_1_hour",
        "1_to_3_hours",
        "over_3_hours",
    ]
    observation_mode: ObservationMode


class FactsPreferences(BaseModel):
    feature: Literal["facts"] = "facts"

    explanation_level: Literal["simple", "detailed"]
    interest: Literal[
        "science",
        "history",
        "general",
    ]


Preferences = Annotated[
    Union[
        LocationPreferences,
        EquipmentPreferences,
        PlanPreferences,
        FactsPreferences,
    ],
    Field(discriminator="feature"),
]


class RecommendationRequest(BaseModel):
    event: AstronomicalEvent
    preferences: Preferences
