
# Bitly-Lite — URL Shortening Service with Analytics
### DSA-PROJECT | Variant B3 | Python

> A mini URL shortening system demonstrating **all 6 required data structures** from the BIT2203 Data Structures & Algorithms course, following the **Chapter 23 five-step system design** process (Hemant Jain).

---

## Problem Statement

Design and implement a simplified URL shortening service (like Bitly) that:
- Shortens long URLs to compact codes
- Resolves short codes back to originals
- Tracks click analytics asynchronously
- Surfaces top-k most-clicked links via a priority queue
- Supports undo, delete, search, and referrer graph traversal

---

## Data Structures & Algorithms Used

| Data Structure | Location | Operation | Big-O |
|---|---|---|---|
| **Hash Map** (dict) | `url_store.py` | shorten / resolve | O(1) avg |
| **Stack** (list LIFO) | `url_store.py` | undo_last() | O(1) |
| **Queue** (deque) | `url_store.py` | click event buffer | O(1) |
| **Max-Heap** (heapq) | `url_store.py` / `analytics.py` | top-k links | O(n log k) |
| **Graph** (dict of sets) | `url_store.py` | referrer BFS | O(V + E) |
| **Binary Search + Tim-sort** | `url_store.py` | prefix search / ranking | O(n log n) |

---

## Architecture Diagram

```
  USER / CLI  ──────►  cli.py  (Interface Layer)
                              │
              ┌───────────────┼──────────────────┐
              ▼                                          ▼                                                   ▼
         analytics.py                         url_store.py                                 benchmark.py
         (Analytics)                          (Core Engine)                                (Perf Tests)
                                                                      │
         ┌────────────────────┼───────────────────────────────────────┐
         ▼                              ▼                              ▼                             ▼                               ▼                                   ▼
   Hash Map (dict)      Stack (list)            Queue (deque)     Heap (heapq)       Graph (dict→set)     Sort/Search
   shorten/resolve      undo history            click events       top-k analytics      referrer BFS           Tim-sort + BinSearch
                   
                            
```

---

## File Structure

```
bitly_lite/
├── cli.py                  # Interactive CLI — run this
├── src/
│   ├── __init__.py
│   ├── url_store.py        # Core engine (all 6 data structures)
│   └── analytics.py        # Analytics layer (top-k, dashboard)
├── tests/
│   └── test_url_store.py   # 36 unit tests (all passing)
├── benchmark/
│   └── benchmark.py        # Big-O empirical benchmark
├── docs/
│   └── System_Design_Report.pdf
└── README.md
```

---

## How to Run

**Requirements:** Python 3.8+, no third-party packages needed.

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/DSA-CH23-GROUP-B3.git
cd DSA-CH23-GROUP-B3

# 2. Run the interactive CLI
python cli.py

# 3. Run the test suite
python tests/test_url_store.py
# or with pytest:
python -m pytest tests/ -v

# 4. Run the benchmark
python benchmark/benchmark.py
```

---

## Sample Inputs / Outputs

### Shorten a URL
```
➜  Enter URL to shorten: https://www.stackoverflow.com
✔  Shortened: http://bitly.lt/a3f92b1
   Stack depth now: 1
```

### Top-K Most Clicked
```
── Top-5 Most Clicked  [Heap O(n log k)] ──────────
  1. gh                   clicks: 7  → https://www.github.com
  2. py                   clicks: 5  → https://www.python.org
  3. a3f92b1              clicks: 3  → https://www.example.com
```

### Test Suite Output
```
Ran 36 tests in 0.008s
OK
```

### Benchmark Output (n=10,000)
```
shorten() per op       0.0027 ms   →  O(1) confirmed
resolve() per op       0.0012 ms   →  O(1) confirmed
top_k(k=5)             0.986 ms    →  O(n log k) confirmed
undo_last()            0.004 ms    →  O(1) confirmed
```

---

## Five-Step Design Process (Chapter 23 — Hemant Jain)

| Step | Summary |
|---|---|
| **1. Use Cases** | 10 use cases across 3 actors (End User, Analytics Consumer, Admin) |
| **2. Constraints** | O(1) shorten/resolve, O(n log k) top-k, in-memory, Python stdlib only |
| **3. Basic Design** | Hash map core + stack/queue/heap/graph/sort as supporting structures |
| **4. Bottlenecks** | Heap staleness → lazy deletion; sync click recording → queue; top-k sort → size-k min-heap |
| **5. Scalability** | Hash-prefix sharding, Redis cache layer, Kafka click queue for production |

Full details in `docs/System_Design_Report.pdf`.

---

## Team Member Roles

| Member | Role |
|---|---|
| ERICSON KARANJA | Back end design and implementation|
| TINAELIS MUMBI| UI design and Documentation|
---


=======
# BITLY-LITE
Bitly-Lite. A URL Shortening Service with Analytics — DSA Project.
>>>>>>> 97c4a93300040bdccc778765b245edab3090f20d
