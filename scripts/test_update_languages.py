from collections import Counter
import unittest
import xml.etree.ElementTree as ET

from update_languages import aggregate, render_card, segments


def page(nodes, more=False, viewer="ExampleOwner"):
    return {"data": {"viewer": {"login": viewer}, "user": {"repositories": {
        "nodes": nodes, "pageInfo": {"hasNextPage": more}
    }}}}


def repo(name, private=False, color="#123456"):
    return {"isPrivate": private,
            "primaryLanguage": None if name is None else {"name": name, "color": color},
            "name": "DO_NOT_PUBLISH_REPOSITORY_NAME", "description": "DO_NOT_PUBLISH_CONTENT"}


class LanguagesTest(unittest.TestCase):
    def test_private_and_public_pages_are_combined_without_counting_empty_repos(self):
        pages = [page([repo("Python", True), repo(None, True)], more=True),
                 page([repo("Python"), repo("Ruby")])]
        counts, _ = aggregate(pages, "exampleowner")
        self.assertEqual(counts, {"Python": 2, "Ruby": 1})

    def test_incomplete_or_public_only_queries_cannot_overwrite_private_cards(self):
        cases = [[], [page([repo("Python")])],
                 [page([repo("Python", True)], more=True)],
                 [page([repo("Python", True)], viewer="SomeoneElse")],
                 [{"errors": [{"message": "private error"}]}]]
        for pages in cases:
            with self.subTest(pages=pages), self.assertRaises(ValueError):
                aggregate(pages, "ExampleOwner")

    def test_other_preserves_total_and_ties_are_stable(self):
        counts = Counter({chr(65 + i): i + 1 for i in range(10)})
        colors = {name: "#123456" for name in counts}
        items = segments(counts, colors)
        self.assertEqual(len(items), 8)
        self.assertEqual(sum(item[1] for item in items), sum(counts.values()))
        self.assertEqual(items[-1], ("Other", 6, "#8b949e"))

    def test_generated_assets_contain_only_escaped_aggregate_values(self):
        counts, colors = aggregate([page([repo('X<&', True, '\" onload=\"bad')])], "ExampleOwner")
        for theme in ("light", "dark"):
            svg = render_card(counts, colors, theme, "2026-01-01")
            root = ET.fromstring(svg)
            self.assertEqual(root.attrib["viewBox"], "0 0 340 200")
            self.assertIn("100.0%", svg)
            self.assertNotIn("DO_NOT_PUBLISH", svg)
            self.assertNotIn("onload", svg)
            self.assertNotIn("<script", svg)
            self.assertIn("X&lt;&amp;", svg)


if __name__ == "__main__":
    unittest.main()
