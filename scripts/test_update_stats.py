import copy
from datetime import datetime, timezone
import json
from unittest import TestCase
from unittest.mock import patch
import xml.etree.ElementTree as ET

import update_stats as stats


def page(repositories, more=False):
    return {"data": {"viewer": {"login": "owner"}, "user": {
        "pullRequests": {"totalCount": 12}, "issues": {"totalCount": 4},
        "repositoriesContributedTo": {"totalCount": 8},
        "contributionsCollection": {"contributionYears": [2026, 2024]},
        "repositories": {"nodes": repositories, "pageInfo": {"hasNextPage": more}},
    }}}


def commits(count, restricted=0):
    return {"data": {"user": {"contributionsCollection": {
        "totalCommitContributions": count, "restrictedContributionsCount": restricted,
    }}}}


class StatsTests(TestCase):
    def test_private_stars_and_pagination_without_repeating_user_totals(self):
        pages = [page([{"isPrivate": False, "stargazerCount": 7}], True),
                 page([{"isPrivate": True, "stargazerCount": 3}])]
        result, years = stats.aggregate_summary(pages, "Owner", 2026)
        self.assertEqual(result, {"stars": 10, "prs": 12, "issues": 4, "contributed_to": 8})
        self.assertEqual(years, [2024, 2026])
        with self.assertRaises(ValueError):
            stats.aggregate_summary(pages[:1], "owner", 2026)
        with self.assertRaises(ValueError):
            stats.aggregate_summary(pages, "someone-else", 2026)
        with self.assertRaises(ValueError):
            stats.aggregate_summary([page([{"isPrivate": False, "stargazerCount": 7}])], "owner", 2026)

    def test_restricted_activity_is_never_added_to_commits(self):
        self.assertEqual(stats.commit_count(commits(30)), 30)
        with self.assertRaises(ValueError):
            stats.commit_count(commits(30, restricted=18))
        with self.assertRaises(ValueError):
            stats.commit_count({"errors": [{"message": "sensitive response"}]})

    def test_token_scopes_guard_against_silent_public_only_counts(self):
        def response(scopes):
            return f'HTTP/2.0 200 OK\r\nX-OAuth-Scopes: {scopes}\r\n\r\n' + json.dumps({"data": {"viewer": {"login": "owner"}}})
        stats.validate_token_response(response("repo, read:user"), "owner")
        for scopes in ("repo", "read:user", "", "public_repo, read:user"):
            with self.subTest(scopes=scopes), self.assertRaises(ValueError):
                stats.validate_token_response(response(scopes), "owner")
        with self.assertRaises(ValueError):
            stats.validate_token_response(response("repo, read:user"), "someone-else")

    def test_all_years_sum_and_nonoverlapping_leap_year_bounds(self):
        now = datetime(2026, 9, 6, tzinfo=timezone.utc)
        self.assertEqual(stats.year_bounds(2024, now),
                         ("2024-01-01T00:00:00+00:00", "2024-12-31T23:59:59+00:00"))
        self.assertEqual(stats.year_bounds(2026, now)[1], now.isoformat())
        responses = [
            'HTTP/2.0 200 OK\nX-Oauth-Scopes: repo, read:user\n\n{"data":{"viewer":{"login":"owner"}}}',
            json.dumps([page([{"isPrivate": True, "stargazerCount": 2}])]),
            json.dumps(commits(31)), json.dumps(commits(47)),
        ]
        with patch.object(stats, "run_gh", side_effect=responses) as api:
            result = stats.fetch_stats("owner", now)
        self.assertEqual(result["commits"], 78)
        self.assertIn("from=2024-01-01T00:00:00+00:00", api.call_args_list[2].args[0])
        self.assertIn("from=2026-01-01T00:00:00+00:00", api.call_args_list[3].args[0])

    def test_invalid_counts_years_and_partial_responses_stop_publication(self):
        fixture = page([{"isPrivate": True, "stargazerCount": 1}])
        for years in ([2026, 2026], [2027], [], ["2026"]):
            invalid = copy.deepcopy(fixture)
            invalid["data"]["user"]["contributionsCollection"]["contributionYears"] = years
            with self.subTest(years=years), self.assertRaises(ValueError):
                stats.aggregate_summary([invalid], "owner", 2026)
        for value in (-1, True, "private-project-name"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                stats.nonnegative_int(value)

    def test_cards_are_valid_xml_and_only_publish_the_explicit_totals(self):
        values = {"stars": 15, "commits": 2345, "prs": 92, "issues": 22,
                  "contributed_to": 61, "private_name": "secret-project"}
        for theme in stats.PALETTES:
            svg = stats.render_card(values, theme, "2026-09-06")
            ET.fromstring(svg)
            self.assertIn("2,345", svg)
            self.assertNotIn("secret-project", svg)
            self.assertNotIn("private_name", svg)
