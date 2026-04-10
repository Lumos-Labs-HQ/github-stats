import unittest
from datetime import date, timedelta, datetime, timezone

from app.github import _build_year_range, _normalize_contributions_api_payload
from app.services.stats import _fmt_date, calculate_streaks


class StreakTests(unittest.TestCase):
    def test_normalize_contributions_api_payload_sorts_days_and_uses_year_totals(self):
        payload = {
            "total": {"2024": 3, "2023": 2},
            "contributions": [
                {"date": "2024-01-02", "count": 2},
                {"date": "2023-12-31", "count": 2},
                {"date": "2024-01-01", "count": 1},
            ],
        }

        normalized = _normalize_contributions_api_payload(payload)

        self.assertEqual(normalized["total_contributions"], 5)
        self.assertEqual(normalized["contribution_totals_by_year"], {"2024": 3, "2023": 2})
        self.assertEqual(
            [day["date"] for day in normalized["days"]],
            ["2023-12-31", "2024-01-01", "2024-01-02"],
        )
        self.assertEqual(normalized["contribution_source"], "github-contributions-api")

    def test_build_year_range_includes_all_years_since_creation(self):
        current_year = datetime.now(timezone.utc).year
        years = _build_year_range(2023, [current_year, 2024, 2023])

        self.assertEqual(years[0], 2023)
        self.assertEqual(years[-1], current_year)
        self.assertEqual(years, list(range(2023, current_year + 1)))

    def test_build_year_range_preserves_pre_2005_backdated_contributions(self):
        current_year = datetime.now(timezone.utc).year
        years = _build_year_range(2023, [2024, 1970])

        self.assertEqual(years[0], 1970)
        self.assertEqual(years[1:], list(range(2023, current_year + 1)))

    def test_calculate_streaks_supports_longer_than_one_year_runs(self):
        today = datetime.now(timezone.utc).date()
        streak_length = 400
        start = today - timedelta(days=streak_length - 1)

        days = [
            {"date": (start + timedelta(days=offset)).isoformat(), "count": 1}
            for offset in range(streak_length)
        ]

        streaks = calculate_streaks(days)

        self.assertEqual(streaks["current_streak"], streak_length)
        self.assertEqual(streaks["longest_streak"], streak_length)
        self.assertIsNotNone(streaks["current_streak_start"])
        self.assertIsNotNone(streaks["longest_streak_start"])

    def test_calculate_streaks_counts_github_tomorrow_square_when_present(self):
        today = datetime.now(timezone.utc).date()
        tomorrow = today + timedelta(days=1)
        start = today - timedelta(days=2)

        days = [
            {"date": (start + timedelta(days=offset)).isoformat(), "count": 1}
            for offset in range(3)
        ] + [{"date": tomorrow.isoformat(), "count": 2}]

        streaks = calculate_streaks(days)

        self.assertEqual(streaks["current_streak"], 4)

    def test_calculate_streaks_preserves_yesterday_streak_when_today_is_zero(self):
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=4)
        days = [
            {"date": (start + timedelta(days=offset)).isoformat(), "count": 1}
            for offset in range(4)
        ] + [{"date": today.isoformat(), "count": 0}]

        streaks = calculate_streaks(days)

        self.assertEqual(streaks["current_streak"], 4)
        self.assertEqual(streaks["current_streak_end"], _fmt_date(today - timedelta(days=1), today.year))


if __name__ == "__main__":
    unittest.main()
