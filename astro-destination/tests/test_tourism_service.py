"""Unit tests for tourism statistics and data processing."""

import unittest

import pandas as pd

from src.tourism_service import TourismDataError, TourismService


TOTAL_ORIGIN = "0 Država - SKUPAJ"
OVERNIGHT_STAYS = "Prenočitve turistov"


def make_row(month, municipality, value,
             origin=TOTAL_ORIGIN, measure=OVERNIGHT_STAYS):
    """Create one PC-Axis data row for testing."""
    return {
        "MESEC": month,
        "OBČINE": municipality,
        "DRŽAVA": origin,
        "MERITVE": measure,
        "DATA": value,
    }


def sample_data():
    """Build a small dataset with known statistical results."""
    rows = []

    # Bohinj: complete 2025 and incomplete 2026.
    for month in range(1, 13):
        rows.append(
            make_row(f"2025M{month:02d}", "Bohinj", month * 100)
        )

    for month in range(1, 10):
        rows.append(
            make_row(f"2026M{month:02d}", "Bohinj", month * 200)
        )

    # Bled: complete 2025 and incomplete 2026.
    for month in range(1, 13):
        rows.append(
            make_row(f"2025M{month:02d}", "Bled", month * 300)
        )

    for month in range(1, 10):
        rows.append(
            make_row(f"2026M{month:02d}", "Bled", month * 400)
        )

    # Rows that must not affect overnight-stay statistics.
    rows.extend([
        make_row(
            "2026M01",
            "Bohinj",
            99999,
            origin="Avstrija",
        ),
        make_row(
            "2026M01",
            "Bohinj",
            88888,
            measure="Prihodi turistov",
        ),
    ])

    return pd.DataFrame(rows)


class TestTourismService(unittest.TestCase):
    """Verify filtering, aggregations, and input validation."""

    def setUp(self):
        """Create a fresh service for each test."""
        self.service = TourismService(sample_data())

    def test_municipalities(self):
        """Return municipality names in alphabetical order."""
        self.assertEqual(
            self.service.municipalities(),
            ["Bled", "Bohinj"],
        )

    def test_available_years(self):
        """Return years available for the selected municipality."""
        self.assertEqual(
            self.service.available_years("Bohinj"),
            [2025, 2026],
        )

    def test_filters_other_origins(self):
        """Exclude individual origin countries to avoid double counting."""
        monthly = self.service.monthly_overnights("Bohinj", 2026)

        self.assertEqual(
            monthly.loc[monthly["month"] == 1, "overnights"].iloc[0],
            200,
        )

    def test_filters_tourist_arrivals(self):
        """Count overnight stays, not tourist arrivals."""
        monthly = self.service.monthly_overnights("Bohinj", 2026)

        self.assertEqual(
            monthly.loc[monthly["month"] == 1, "overnights"].iloc[0],
            200,
        )

    def test_monthly_overnights(self):
        """Return correct monthly overnight-stay values."""
        monthly = self.service.monthly_overnights("Bohinj", 2025)

        self.assertEqual(len(monthly), 12)
        self.assertEqual(monthly["overnights"].iloc[0], 100)
        self.assertEqual(monthly["overnights"].iloc[11], 1200)
        self.assertEqual(
            monthly["overnights"].sum(),
            7800,
        )

    def test_missing_months(self):
        """Keep unavailable months missing instead of treating them as zero."""
        monthly = self.service.monthly_overnights("Bohinj", 2026)

        self.assertEqual(len(monthly), 12)
        self.assertEqual(monthly["overnights"].count(), 9)

        for month in (10, 11, 12):
            value = monthly.loc[
                monthly["month"] == month,
                "overnights",
            ].iloc[0]

            self.assertTrue(pd.isna(value))

    def test_compare_municipalities(self):
        """Compare both municipalities in the same year."""
        comparison = self.service.compare_municipalities(
            "Bohinj",
            "Bled",
            2025,
        )

        self.assertEqual(len(comparison), 12)

        january = comparison.loc[
            comparison["month"] == 1
        ].iloc[0]

        self.assertEqual(january["first_overnights"], 100)
        self.assertEqual(january["second_overnights"], 300)

    def test_extreme_months(self):
        """Find the busiest and quietest available months."""
        extremes = self.service.extreme_months("Bohinj", 2026)

        self.assertEqual(
            extremes["most_visited"]["overnights"],
            1800,
        )
        self.assertEqual(
            extremes["least_visited"]["overnights"],
            200,
        )

    def test_annual_trends(self):
        """Calculate annual totals without duplicating filtered data."""
        trends = self.service.annual_trends("Bohinj")

        year_2025 = trends.loc[
            trends["year"] == 2025
        ].iloc[0]

        year_2026 = trends.loc[
            trends["year"] == 2026
        ].iloc[0]

        self.assertEqual(year_2025["total_overnights"], 7800)
        self.assertEqual(year_2025["available_months"], 12)
        self.assertTrue(year_2025["complete_year"])

        self.assertEqual(year_2026["total_overnights"], 9000)
        self.assertEqual(year_2026["available_months"], 9)
        self.assertFalse(year_2026["complete_year"])

    def test_missing_columns(self):
        """Reject input without all required PC-Axis columns."""
        invalid_data = sample_data().drop(columns=["MERITVE"])

        with self.assertRaises(TourismDataError):
            TourismService(invalid_data)

    def test_duplicate_records(self):
        """Reject duplicate municipality, year, and month records."""
        data = sample_data()

        duplicate = make_row("2025M01", "Bohinj", 100)

        data = pd.concat(
            [data, pd.DataFrame([duplicate])],
            ignore_index=True,
        )

        with self.assertRaises(TourismDataError):
            TourismService(data)

    def test_unknown_municipality(self):
        """Reject municipalities not present in the dataset."""
        with self.assertRaises(TourismDataError):
            self.service.available_years("Unknown municipality")

    def test_empty_input(self):
        """Reject empty datasets containing no valid statistics."""
        empty_data = pd.DataFrame(
            columns=["MESEC", "OBČINE", "DRŽAVA", "MERITVE", "DATA"]
        )

        with self.assertRaises(TourismDataError):
            TourismService(empty_data)


if __name__ == "__main__":
    unittest.main()
