
"""Process tourism statistics from the SURS PC-Axis dataset."""

import pandas as pd


TOTAL_ORIGIN = "0 Država - SKUPAJ"
OVERNIGHT_STAYS = "Prenočitve turistov"

MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


class TourismDataError(ValueError):
    """Raised when tourism data or a requested selection is invalid."""


class TourismService:
    """Provide tourism statistics for Slovenian municipalities."""

    def __init__(self, data: pd.DataFrame):
        """Validate and prepare the parsed PC-Axis dataset."""
        required_columns = {
            "MESEC", "OBČINE", "DRŽAVA", "MERITVE", "DATA"
        }

        if not required_columns.issubset(data.columns):
            missing = required_columns - set(data.columns)
            raise TourismDataError(
                f"Missing required columns: {sorted(missing)}"
            )

        # Select total overnight stays without double-counting origins.
        mask = (
            (data["DRŽAVA"] == TOTAL_ORIGIN)
            & (data["MERITVE"] == OVERNIGHT_STAYS)
        )

        self.data = data.loc[
            mask, ["MESEC", "OBČINE", "DATA"]
        ].copy()

        if self.data.empty:
            raise TourismDataError(
                "No total overnight stay records were found."
            )

        # Parse PC-Axis monthly labels such as 2026M09.
        periods = self.data["MESEC"].astype(str).str.extract(
            r"^(\d{4})M(0[1-9]|1[0-2])$"
        )

        if periods.isna().any().any():
            raise TourismDataError(
                "The dataset contains invalid month labels."
            )

        self.data["year"] = periods[0].astype(int)
        self.data["month"] = periods[1].astype(int)

        # Missing or suppressed statistical values remain missing.
        self.data["overnights"] = pd.to_numeric(
            self.data["DATA"], errors="coerce"
        )

        self.data = self.data.drop(
            columns=["MESEC", "DATA"]
        )

        if self.data["overnights"].notna().sum() == 0:
            raise TourismDataError(
                "No valid overnight stay values were found."
            )

        if self.data.duplicated(
            subset=["OBČINE", "year", "month"]
        ).any():
            raise TourismDataError(
                "Duplicate monthly records were found."
            )

    def municipalities(self) -> list[str]:
        """Return available municipalities in alphabetical order."""
        return sorted(self.data["OBČINE"].unique().tolist())

    def available_years(self, municipality: str) -> list[int]:
        """Return years with available data for a municipality."""
        records = self._municipality_data(municipality)
        years = records.loc[
            records["overnights"].notna(), "year"
        ]
        return sorted(years.unique().tolist())

    def _municipality_data(
        self, municipality: str
    ) -> pd.DataFrame:
        """Return records belonging to the selected municipality."""
        records = self.data[
            self.data["OBČINE"] == municipality
        ]

        if records.empty:
            raise TourismDataError(
                f"Unknown municipality: {municipality}"
            )

        return records

    def monthly_overnights(
        self, municipality: str, year: int
    ) -> pd.DataFrame:
        """Return monthly overnight stays for a municipality and year."""
        records = self._municipality_data(municipality)
        records = records[records["year"] == year]

        if records.empty:
            raise TourismDataError(
                f"No data for {municipality} in {year}."
            )

        result = records[
            ["month", "overnights"]
        ].set_index("month")

        # Keep all months visible, including unavailable months.
        result = result.reindex(range(1, 13))
        result.index.name = "month"
        result = result.reset_index()

        result["month_name"] = result["month"].map(MONTH_NAMES)

        return result[
            ["month", "month_name", "overnights"]
        ]

    def compare_municipalities(
        self, first: str, second: str, year: int
    ) -> pd.DataFrame:
        """Compare monthly overnight stays for two municipalities."""
        first_data = self.monthly_overnights(first, year)
        second_data = self.monthly_overnights(second, year)

        result = first_data.rename(
            columns={"overnights": "first_overnights"}
        )

        result["second_overnights"] = (
            second_data["overnights"].to_numpy()
        )

        return result

    def extreme_months(
        self, municipality: str, year: int
    ) -> dict:
        """Find the months with most and fewest overnight stays."""
        monthly = self.monthly_overnights(
            municipality, year
        ).dropna(subset=["overnights"])

        if monthly.empty:
            raise TourismDataError(
                f"No valid overnight stays for {municipality} in {year}."
            )

        highest = monthly.loc[monthly["overnights"].idxmax()]
        lowest = monthly.loc[monthly["overnights"].idxmin()]

        return {
            "municipality": municipality,
            "year": year,
            "most_visited": {
                "month": highest["month_name"],
                "overnights": int(highest["overnights"]),
            },
            "least_visited": {
                "month": lowest["month_name"],
                "overnights": int(lowest["overnights"]),
            },
        }

    def annual_trends(self, municipality: str) -> pd.DataFrame:
        """Calculate annual totals and indicate incomplete years."""
        records = self._municipality_data(municipality)

        result = (
            records.groupby("year")["overnights"]
            .agg(
                total_overnights=lambda values: values.sum(
                    min_count=1
                ),
                available_months="count",
            )
            .reset_index()
            .sort_values("year")
        )

        result["complete_year"] = (
            result["available_months"] == 12
        )

        return result
