
import heapq
import time
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .url_store import URLStore


class Analytics:


    def __init__(self, store: "URLStore"):
        self._store = store


    def top_k_links(self, k: int = 5) -> list[dict]:

        all_records = self._store.all_urls()
        if not all_records:
            return []

        heap = []
        for record in all_records:
            clicks = record["clicks"]
            if len(heap) < k:
                heapq.heappush(heap, (clicks, record["short_code"], record))
            elif clicks > heap[0][0]:
                heapq.heapreplace(heap, (clicks, record["short_code"], record))

        return [item[2] for item in sorted(heap, key=lambda x: -x[0])]


    def clicks_per_day(self, short_code: str) -> dict[str, int]:

        daily: dict[str, int] = defaultdict(int)
        for (code, ts, _ref) in list(self._store._click_queue):
            if code == short_code:
                day_key = time.strftime("%Y-%m-%d", time.localtime(ts))
                daily[day_key] += 1
        return dict(daily)


    def referrer_breakdown(self) -> dict[str, int]:

        result = {}
        for ref, codes in self._store._referrer_graph.items():
            result[ref] = len(codes)
        return dict(sorted(result.items(), key=lambda x: -x[1]))


    def sorted_report(self) -> list[dict]:

        return self._store.all_sorted_by_clicks()


    def dashboard(self) -> dict:

        all_records = self._store.all_urls()
        total_clicks = sum(r["clicks"] for r in all_records)
        return {
            "total_urls":     len(all_records),
            "total_clicks":   total_clicks,
            "queue_depth":    self._store.queue_depth(),
            "stack_depth":    self._store.stack_depth(),
            "top_3":          self.top_k_links(3),
        }