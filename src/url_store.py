
import hashlib
import time
import heapq
from collections import deque, defaultdict
from typing import Optional


class URLStore:

    BASE_URL = "http://bitly.lt/"
    CODE_LEN  = 7

    def __init__(self):
        self._short_to_data: dict[str, dict] = {}
        self._long_to_short: dict[str, str]  = {}

        self._history_stack: list[tuple] = []

        self._click_queue: deque = deque()

        self._REMOVED = "<removed>"
        self._click_heap: list[tuple] = []
        self._heap_entry_map: dict[str, list] = {}

        self._referrer_graph: dict[str, set] = defaultdict(set)

    def shorten(self, original_url: str, alias: Optional[str] = None) -> str:
        if original_url in self._long_to_short:
            return self.BASE_URL + self._long_to_short[original_url]

        if alias:
            if alias in self._short_to_data:
                raise ValueError(f"Alias '{alias}' already taken.")
            code = alias
        else:
            code = self._generate_code(original_url)

        metadata = {
            "original_url": original_url,
            "short_code":   code,
            "created_at":   time.time(),
            "clicks":       0,
            "alias":        bool(alias),
        }
        self._short_to_data[code] = metadata
        self._long_to_short[original_url] = code

        self._history_stack.append(("SHORTEN", code))

        entry = [0, code]
        self._heap_entry_map[code] = entry
        heapq.heappush(self._click_heap, entry)

        return self.BASE_URL + code

    def resolve(self, short_code: str, referrer: str = "direct") -> Optional[str]:
        code = short_code.replace(self.BASE_URL, "")
        if code not in self._short_to_data:
            return None

        self._short_to_data[code]["clicks"] += 1

        self._click_queue.append((code, time.time(), referrer))

        self._referrer_graph[referrer].add(code)

        return self._short_to_data[code]["original_url"]

    def process_click_queue(self) -> int:
        processed = 0
        while self._click_queue:
            code, _ts, _ref = self._click_queue.popleft()
            if code in self._heap_entry_map:
                clicks = self._short_to_data[code]["clicks"]
                old_entry = self._heap_entry_map[code]
                old_entry[1] = self._REMOVED
                new_entry = [-clicks, code]
                self._heap_entry_map[code] = new_entry
                heapq.heappush(self._click_heap, new_entry)
            processed += 1
        return processed

    def top_k(self, k: int = 5) -> list[dict]:
        self.process_click_queue()
        results = []
        seen = set()

        heap_copy = list(self._click_heap)
        heapq.heapify(heap_copy)

        while heap_copy and len(results) < k:
            neg_clicks, code = heapq.heappop(heap_copy)
            if code == self._REMOVED or code in seen:
                continue
            seen.add(code)
            if code in self._short_to_data:
                entry = self._short_to_data[code].copy()
                entry["clicks"] = -neg_clicks
                results.append(entry)

        return results

    def undo_last(self) -> Optional[str]:
        if not self._history_stack:
            return None
        action, code = self._history_stack.pop()
        if action == "SHORTEN" and code in self._short_to_data:
            meta = self._short_to_data.pop(code)
            self._long_to_short.pop(meta["original_url"], None)
            if code in self._heap_entry_map:
                self._heap_entry_map[code][1] = self._REMOVED
                del self._heap_entry_map[code]
            return f"Undone: removed short code '{code}'"
        return None

    def delete(self, short_code: str) -> bool:
        code = short_code.replace(self.BASE_URL, "")
        if code not in self._short_to_data:
            return False
        meta = self._short_to_data.pop(code)
        self._long_to_short.pop(meta["original_url"], None)
        self._history_stack.append(("DELETE", code))
        if code in self._heap_entry_map:
            self._heap_entry_map[code][1] = self._REMOVED
            del self._heap_entry_map[code]
        return True

    def referrer_bfs(self, start_referrer: str) -> list[str]:
        if start_referrer not in self._referrer_graph:
            return []

        visited_referrers = set()
        visited_codes = []
        queue = deque([start_referrer])

        while queue:
            referrer = queue.popleft()
            if referrer in visited_referrers:
                continue
            visited_referrers.add(referrer)
            for code in self._referrer_graph[referrer]:
                visited_codes.append(code)
                for ref, codes in self._referrer_graph.items():
                    if code in codes and ref not in visited_referrers:
                        queue.append(ref)

        return visited_codes

    def search_by_prefix(self, prefix: str) -> list[str]:
        codes = sorted(self._short_to_data.keys())
        lo, hi = 0, len(codes)
        while lo < hi:
            mid = (lo + hi) // 2
            if codes[mid] < prefix:
                lo = mid + 1
            else:
                hi = mid
        results = []
        i = lo
        while i < len(codes) and codes[i].startswith(prefix):
            results.append(codes[i])
            i += 1
        return results

    def all_sorted_by_clicks(self) -> list[dict]:
        return sorted(
            self._short_to_data.values(),
            key=lambda x: x["clicks"],
            reverse=True
        )

    def _generate_code(self, url: str) -> str:
        counter = 0
        while True:
            raw = f"{url}{time.time()}{counter}".encode()
            code = hashlib.md5(raw).hexdigest()[:self.CODE_LEN]
            if code not in self._short_to_data:
                return code
            counter += 1

    def stats(self, short_code: str) -> Optional[dict]:
        code = short_code.replace(self.BASE_URL, "")
        return self._short_to_data.get(code)

    def all_urls(self) -> list[dict]:
        return list(self._short_to_data.values())

    def stack_depth(self) -> int:
        return len(self._history_stack)

    def queue_depth(self) -> int:
        return len(self._click_queue)