
import sys
import os
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.url_store import URLStore
from src.analytics import Analytics


class TestHashMap(unittest.TestCase):

    def setUp(self):
        self.store = URLStore()

    def test_shorten_returns_url(self):
        short = self.store.shorten("https://example.com")
        self.assertTrue(short.startswith(URLStore.BASE_URL))

    def test_shorten_idempotent(self):
        a = self.store.shorten("https://example.com")
        b = self.store.shorten("https://example.com")
        self.assertEqual(a, b)

    def test_different_urls_different_codes(self):
        a = self.store.shorten("https://alpha.com")
        b = self.store.shorten("https://beta.com")
        self.assertNotEqual(a, b)

    def test_resolve_returns_original(self):
        original = "https://example.com"
        short = self.store.shorten(original)
        code = short.replace(URLStore.BASE_URL, "")
        self.assertEqual(self.store.resolve(code), original)

    def test_resolve_invalid_code_returns_none(self):
        self.assertIsNone(self.store.resolve("XXXXXXX"))

    def test_alias_shorten(self):
        short = self.store.shorten("https://github.com", alias="gh")
        self.assertEqual(short, URLStore.BASE_URL + "gh")

    def test_alias_collision_raises(self):
        self.store.shorten("https://github.com", alias="gh")
        with self.assertRaises(ValueError):
            self.store.shorten("https://gitlab.com", alias="gh")

    def test_stats_after_shorten(self):
        self.store.shorten("https://example.com", alias="ex")
        meta = self.store.stats("ex")
        self.assertIsNotNone(meta)
        self.assertEqual(meta["original_url"], "https://example.com")
        self.assertEqual(meta["clicks"], 0)

    def test_click_count_increments(self):
        self.store.shorten("https://example.com", alias="ex")
        self.store.resolve("ex")
        self.store.resolve("ex")
        meta = self.store.stats("ex")
        self.assertEqual(meta["clicks"], 2)

    def test_delete_removes_entry(self):
        self.store.shorten("https://example.com", alias="ex")
        self.store.delete("ex")
        self.assertIsNone(self.store.stats("ex"))

    def test_delete_nonexistent_returns_false(self):
        self.assertFalse(self.store.delete("NOPE"))


class TestStack(unittest.TestCase):

    def setUp(self):
        self.store = URLStore()

    def test_undo_removes_last_shorten(self):
        self.store.shorten("https://example.com", alias="ex")
        self.store.undo_last()
        self.assertIsNone(self.store.stats("ex"))

    def test_undo_empty_stack_returns_none(self):
        self.assertIsNone(self.store.undo_last())

    def test_undo_twice(self):
        self.store.shorten("https://alpha.com", alias="a")
        self.store.shorten("https://beta.com",  alias="b")
        self.store.undo_last()
        self.assertIsNone(self.store.stats("b"))
        self.assertIsNotNone(self.store.stats("a"))
        self.store.undo_last()
        self.assertIsNone(self.store.stats("a"))

    def test_stack_depth_increases(self):
        self.assertEqual(self.store.stack_depth(), 0)
        self.store.shorten("https://alpha.com")
        self.assertEqual(self.store.stack_depth(), 1)
        self.store.shorten("https://beta.com")
        self.assertEqual(self.store.stack_depth(), 2)

    def test_stack_depth_decreases_on_undo(self):
        self.store.shorten("https://alpha.com")
        self.store.shorten("https://beta.com")
        self.store.undo_last()
        self.assertEqual(self.store.stack_depth(), 1)


class TestQueue(unittest.TestCase):

    def setUp(self):
        self.store = URLStore()

    def test_resolve_enqueues_event(self):
        self.store.shorten("https://example.com", alias="ex")
        self.store.resolve("ex")
        self.assertEqual(self.store.queue_depth(), 1)

    def test_multiple_resolves_queue_multiple_events(self):
        self.store.shorten("https://example.com", alias="ex")
        for _ in range(5):
            self.store.resolve("ex")
        self.assertEqual(self.store.queue_depth(), 5)

    def test_process_queue_drains_all(self):
        self.store.shorten("https://example.com", alias="ex")
        for _ in range(3):
            self.store.resolve("ex")
        processed = self.store.process_click_queue()
        self.assertEqual(processed, 3)
        self.assertEqual(self.store.queue_depth(), 0)

    def test_queue_empty_after_drain(self):
        self.store.shorten("https://example.com", alias="ex")
        self.store.resolve("ex")
        self.store.process_click_queue()
        self.assertEqual(self.store.queue_depth(), 0)


class TestHeap(unittest.TestCase):

    def setUp(self):
        self.store = URLStore()
        self.analytics = Analytics(self.store)

    def test_topk_returns_correct_order(self):
        self.store.shorten("https://a.com", alias="a")
        self.store.shorten("https://b.com", alias="b")
        self.store.shorten("https://c.com", alias="c")
        for _ in range(5): self.store.resolve("c")
        for _ in range(2): self.store.resolve("a")
        self.store.resolve("b")
        self.store.process_click_queue()
        top = self.analytics.top_k_links(3)
        self.assertEqual(top[0]["short_code"], "c")
        self.assertEqual(top[1]["short_code"], "a")
        self.assertEqual(top[2]["short_code"], "b")

    def test_topk_with_k_larger_than_urls(self):
        self.store.shorten("https://only.com", alias="only")
        top = self.analytics.top_k_links(10)
        self.assertEqual(len(top), 1)

    def test_topk_empty_store(self):
        top = self.analytics.top_k_links(5)
        self.assertEqual(top, [])

    def test_dashboard_top3(self):
        for i in range(5):
            self.store.shorten(f"https://site{i}.com", alias=f"s{i}")
            for _ in range(i + 1):
                self.store.resolve(f"s{i}")
        self.store.process_click_queue()
        dash = self.analytics.dashboard()
        self.assertEqual(len(dash["top_3"]), 3)
        self.assertEqual(dash["top_3"][0]["short_code"], "s4")


class TestGraph(unittest.TestCase):

    def setUp(self):
        self.store = URLStore()

    def test_referrer_recorded(self):
        self.store.shorten("https://example.com", alias="ex")
        self.store.resolve("ex", referrer="twitter.com")
        self.assertIn("ex", self.store._referrer_graph["twitter.com"])

    def test_bfs_returns_codes(self):
        self.store.shorten("https://a.com", alias="a")
        self.store.shorten("https://b.com", alias="b")
        self.store.resolve("a", referrer="google.com")
        self.store.resolve("b", referrer="google.com")
        codes = self.store.referrer_bfs("google.com")
        self.assertIn("a", codes)
        self.assertIn("b", codes)

    def test_bfs_unknown_referrer_returns_empty(self):
        codes = self.store.referrer_bfs("nowhere.com")
        self.assertEqual(codes, [])


class TestSortingAndSearch(unittest.TestCase):

    def setUp(self):
        self.store = URLStore()

    def test_sorted_by_clicks_descending(self):
        for i, alias in enumerate(["a", "b", "c"]):
            self.store.shorten(f"https://{alias}.com", alias=alias)
            for _ in range(i + 1):
                self.store.resolve(alias)
        sorted_list = self.store.all_sorted_by_clicks()
        self.assertGreaterEqual(sorted_list[0]["clicks"], sorted_list[1]["clicks"])
        self.assertGreaterEqual(sorted_list[1]["clicks"], sorted_list[2]["clicks"])

    def test_search_prefix_finds_matches(self):
        self.store.shorten("https://github.com", alias="gh")
        results = self.store.search_by_prefix("g")
        self.assertIn("gh", results)

    def test_search_prefix_no_match(self):
        results = self.store.search_by_prefix("zzz")
        self.assertEqual(results, [])

    def test_search_prefix_empty_store(self):
        results = self.store.search_by_prefix("a")
        self.assertEqual(results, [])


class TestEdgeCases(unittest.TestCase):

    def setUp(self):
        self.store = URLStore()

    def test_empty_url_store_stats(self):
        self.assertIsNone(self.store.stats("nonexistent"))

    def test_resolve_after_delete_returns_none(self):
        self.store.shorten("https://example.com", alias="ex")
        self.store.delete("ex")
        self.assertIsNone(self.store.resolve("ex"))

    def test_all_urls_empty(self):
        self.assertEqual(self.store.all_urls(), [])

    def test_many_urls_no_collision(self):
        import random, string
        codes = set()
        for _ in range(500):
            url = "https://" + ''.join(random.choices(string.ascii_lowercase, k=12)) + ".com"
            short = self.store.shorten(url)
            code = short.replace(URLStore.BASE_URL, "")
            codes.add(code)
        self.assertEqual(len(codes), 500)

    def test_undo_after_delete_does_not_restore(self):
        self.store.shorten("https://example.com", alias="ex")
        self.store.delete("ex")
        result = self.store.undo_last()
        self.assertIsNone(self.store.stats("ex"))


if __name__ == "__main__":
    print("\n" + "═"*55)
    print("  BITLY-LITE  –  UNIT TEST SUITE")
    print("═"*55 + "\n")
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestHashMap, TestStack, TestQueue,
                TestHeap, TestGraph, TestSortingAndSearch, TestEdgeCases]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
