

import sys
import os
import time
import random
import string

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.url_store import URLStore
from src.analytics import Analytics



def random_url():
    slug = ''.join(random.choices(string.ascii_lowercase, k=10))
    return f"https://example.com/{slug}"

def random_referrer():
    return random.choice(["google.com", "twitter.com", "direct", "email", "reddit.com"])

def time_op(label: str, fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000  # ms
    print(f"  {label:<45s}  {elapsed:>8.3f} ms")
    return result



def bench_shorten(store: URLStore, n: int):
    
    urls = [random_url() for _ in range(n)]
    start = time.perf_counter()
    for url in urls:
        store.shorten(url)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  shorten() x{n:<6}                               {elapsed:>8.3f} ms  "
          f"({elapsed/n:.4f} ms/op)")

def bench_resolve(store: URLStore, codes: list[str], n: int):
   
    sample = [random.choice(codes) for _ in range(n)]
    start = time.perf_counter()
    for code in sample:
        store.resolve(code, referrer=random_referrer())
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  resolve() x{n:<6}                               {elapsed:>8.3f} ms  "
          f"({elapsed/n:.4f} ms/op)")

def bench_topk(store: URLStore, k: int):
    store.process_click_queue()
    time_op(f"top_k(k={k})", store.top_k, k)

def bench_sort(store: URLStore):
    time_op("all_sorted_by_clicks()  O(n log n)", store.all_sorted_by_clicks)

def bench_search(store: URLStore, prefix: str):
    time_op(f"search_by_prefix('{prefix}')  O(n log n)+O(log n)", store.search_by_prefix, prefix)

def bench_undo(store: URLStore):

    store.shorten(random_url())
    time_op("undo_last()  O(1)", store.undo_last)

def bench_queue(store: URLStore):

    time_op(f"process_click_queue() ({store.queue_depth()} events)", store.process_click_queue)

def bench_bfs(store: URLStore):

    referrers = list(store._referrer_graph.keys())
    if not referrers:
        print("  referrer_bfs() – no referrers yet"); return
    ref = referrers[0]
    time_op(f"referrer_bfs('{ref}')  O(V+E)", store.referrer_bfs, ref)


def run_benchmark():
    SIZES = [100, 1_000, 5_000, 10_000]

    print("\n" + "═"*65)
    print("  BITLY-LITE  –  DSA BENCHMARK REPORT")
    print("═"*65)

    for n in SIZES:
        store = URLStore()
        print(f"\n{'─'*65}")
        print(f"  Dataset size: n = {n:,} URLs")
        print(f"{'─'*65}")


        bench_shorten(store, n)
        all_codes = list(store._short_to_data.keys())
        
        bench_resolve(store, all_codes, min(n, 1000))

        bench_topk(store, 5)
        bench_topk(store, 10)

        bench_sort(store)

        if all_codes:
            prefix = all_codes[0][:2]
            bench_search(store, prefix)

        bench_undo(store)

        bench_queue(store)

        bench_bfs(store)

    print("\n" + "═"*65)
    print("  COMPLEXITY SUMMARY")
    print("═"*65)
    rows = [
        ("shorten()",              "O(1) avg",        "O(n)"),
        ("resolve()",              "O(1) avg",        "O(n)"),
        ("top_k(k)",               "O(n log k)",      "O(k)"),
        ("undo_last()",            "O(1)",             "O(n)"),
        ("process_click_queue()",  "O(k log n)",       "O(n)"),
        ("search_by_prefix()",     "O(n log n)+O(log n)", "O(n)"),
        ("referrer_bfs()",         "O(V + E)",        "O(V)"),
        ("all_sorted_by_clicks()", "O(n log n)",      "O(n)"),
    ]
    print(f"\n  {'Operation':<30}  {'Time':<20}  {'Space'}")
    print(f"  {'─'*30}  {'─'*20}  {'─'*10}")
    for op, time_c, space_c in rows:
        print(f"  {op:<30}  {time_c:<20}  {space_c}")
    print()


if __name__ == "__main__":
    run_benchmark()
