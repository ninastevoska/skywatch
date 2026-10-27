
"""Integration tests for the AstroDestination FastAPI endpoints."""

import unittest

from fastapi.testclient import TestClient

from main import app, get_tourism_service
from src.tourism_service import TourismService
from tests.test_tourism_service import sample_data


class TestTourismAPI(unittest.TestCase):
    """Verify API responses using a small, predictable dataset."""

    def setUp(self):
        """Replace live SURS data with controlled test data."""
        self.service = TourismService(sample_data())

        app.dependency_overrides[get_tourism_service] = (
            lambda: self.service
        )

        # Without a context manager, TestClient does not run
        # the application's lifespan or download SURS data.
        self.client = TestClient(app)

    def tearDown(self):
        """Remove test dependencies after each test."""
        self.client.close()
        app.dependency_overrides.clear()

    def test_municipalities(self):
        """Return available municipalities."""
        response = self.client.get("/api/municipalities")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["municipalities"],
            ["Bled", "Bohinj"],
        )

    def test_available_years(self):
        """Return years for a selected municipality."""
        response = self.client.get(
            "/api/years",
            params={"municipality": "Bohinj"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["years"],
            [2025, 2026],
        )

    def test_monthly_overnights(self):
        """Return twelve months with correct values."""
        response = self.client.get(
            "/api/monthly",
            params={
                "municipality": "Bohinj",
                "year": 2025,
            },
        )

        self.assertEqual(response.status_code, 200)

        months = response.json()["months"]

        self.assertEqual(len(months), 12)
        self.assertEqual(months[0]["overnights"], 100)
        self.assertEqual(months[11]["overnights"], 1200)

    def test_missing_months_are_null(self):
        """Serialize missing months as JSON null, not zero."""
        response = self.client.get(
            "/api/monthly",
            params={
                "municipality": "Bohinj",
                "year": 2026,
            },
        )

        self.assertEqual(response.status_code, 200)

        months = response.json()["months"]

        self.assertEqual(months[8]["overnights"], 1800)

        for month in months[9:]:
            self.assertIsNone(month["overnights"])

    def test_compare_municipalities(self):
        """Return monthly values for both municipalities."""
        response = self.client.get(
            "/api/compare",
            params={
                "first": "Bohinj",
                "second": "Bled",
                "year": 2025,
            },
        )

        self.assertEqual(response.status_code, 200)

        january = response.json()["months"][0]

        self.assertEqual(january["first_overnights"], 100)
        self.assertEqual(january["second_overnights"], 300)

    def test_extreme_months(self):
        """Return the busiest and quietest months."""
        response = self.client.get(
            "/api/extremes",
            params={
                "municipality": "Bohinj",
                "year": 2026,
            },
        )

        self.assertEqual(response.status_code, 200)

        extremes = response.json()

        self.assertEqual(
            extremes["most_visited"]["overnights"],
            1800,
        )
        self.assertEqual(
            extremes["least_visited"]["overnights"],
            200,
        )

    def test_annual_trends(self):
        """Distinguish complete and incomplete years."""
        response = self.client.get(
            "/api/trends",
            params={"municipality": "Bohinj"},
        )

        self.assertEqual(response.status_code, 200)

        years = {
            item["year"]: item
            for item in response.json()["years"]
        }

        self.assertEqual(years[2025]["total_overnights"], 7800)
        self.assertEqual(years[2026]["total_overnights"], 9000)

        self.assertTrue(years[2025]["complete_year"])
        self.assertFalse(years[2026]["complete_year"])

    def test_unknown_municipality(self):
        """Return HTTP 400 for an unknown municipality."""
        response = self.client.get(
            "/api/years",
            params={"municipality": "Unknown municipality"},
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_query_parameter(self):
        """Reject requests without required parameters."""
        response = self.client.get("/api/monthly")

        self.assertEqual(response.status_code, 422)

    def test_invalid_year(self):
        """Reject a nonnumeric year before processing data."""
        response = self.client.get(
            "/api/monthly",
            params={
                "municipality": "Bohinj",
                "year": "invalid",
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
