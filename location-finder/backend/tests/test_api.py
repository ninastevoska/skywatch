import httpx
import pytest


BASE_URL = "http://127.0.0.1:8003"

DISCOVERY_REQUEST = {
    "origin": {
        "coordinates": {
            "latitude": 46.5547,
            "longitude": 15.6459,
        },
        "name": "Maribor",
    },
    "transport_mode": "foot-walking",
    "range_type": "time",
    "range_value": 1800,
    "categories": ["viewpoint", "peak", "saddle"],
    "max_results": 5,
    "sort_by": "duration",
}

ROUTE_REQUEST = {
    "origin": {
        "latitude": 46.5547,
        "longitude": 15.6459,
    },
    "destination": {
        "latitude": 46.568487,
        "longitude": 15.646258,
    },
    "transport_mode": "foot-walking",
}


@pytest.fixture(scope="module")
def client():
    """Create an HTTP client for integration tests."""

    with httpx.Client(
        base_url=BASE_URL,
        timeout=180.0,
    ) as http_client:
        yield http_client


def test_health(client):
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["api_available"] is True
    assert data["worker_available"] is True


def test_geocoding(client):
    response = client.get(
        "/api/locations",
        params={
            "name": "Maribor",
            "limit": 3,
        },
    )

    assert response.status_code == 200

    locations = response.json()["locations"]

    assert 1 <= len(locations) <= 3

    assert any(
        location["name"] == "Maribor"
        and location["country"] == "Slovenia"
        for location in locations
    )


def test_discovery(client):
    response = client.post(
        "/api/discover",
        json=DISCOVERY_REQUEST,
    )

    assert response.status_code == 200, response.text

    data = response.json()
    candidates = data["candidates"]

    assert data["isochrone"]["type"] in {
        "Polygon",
        "MultiPolygon",
    }

    assert 1 <= len(candidates) <= 5
    assert data["total_candidates"] >= len(candidates)

    # Verify that all candidates satisfy the travel time limit.
    durations = [
        candidate["travel_duration_seconds"]
        for candidate in candidates
    ]

    assert all(
        0 <= duration <= 1800
        for duration in durations
    )

    # Verify that candidates are sorted by travel duration.
    assert durations == sorted(durations)

    # Verify that candidate identifiers are unique.
    candidate_ids = [
        candidate["id"]
        for candidate in candidates
    ]

    assert len(candidate_ids) == len(set(candidate_ids))


def test_route(client):
    response = client.post(
        "/api/route",
        json=ROUTE_REQUEST,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["distance_m"] > 0
    assert data["duration_seconds"] > 0

    assert data["geometry"]["type"] == "LineString"
    assert len(data["geometry"]["coordinates"]) >= 2

    print(
        f"\nRoute distance: {data['distance_m']:.2f} m"
    )

    print(
        f"Route duration: "
        f"{data['duration_seconds'] / 60:.2f} min"
    )


def test_invalid_discovery_request(client):
    invalid_request = {
        **DISCOVERY_REQUEST,
        "transport_mode": "driving-car",
        "range_value": 5400,
    }

    response = client.post(
        "/api/discover",
        json=invalid_request,
    )

    assert response.status_code == 422


def test_worker_unavailable(client):
    health = client.get("/api/health")

    assert health.status_code == 200
    assert health.json()["worker_available"] is False

    response = client.post(
        "/api/discover",
        json=DISCOVERY_REQUEST,
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "PIPE_CONNECTION_ERROR"
    )