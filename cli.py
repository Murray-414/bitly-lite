
import sys
import os
import time
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.url_store import URLStore
from src.analytics import Analytics

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def c(text, colour): return f"{colour}{text}{RESET}"
def header(title):
    print(f"\n{BOLD}{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*55}{RESET}")

MENU = """
{bold}{cyan}╔══════════════════════════════════════════════╗
║           BITLY-LITE  URL SHORTENER          ║
║        DSA-CH23 Group Project  –  B3         ║
╚══════════════════════════════════════════════╝{reset}

  {g}[1]{r}  Shorten a URL
  {g}[2]{r}  Shorten with custom alias
  {g}[3]{r}  Resolve / Visit a short link
  {g}[4]{r}  Show stats for a short link
  {g}[5]{r}  Top-K most clicked  {y}(Heap){r}
  {g}[6]{r}  Undo last shorten   {y}(Stack){r}
  {g}[7]{r}  Delete a short link
  {g}[8]{r}  Search by code prefix {y}(Binary Search){r}
  {g}[9]{r}  BFS on referrer graph  {y}(Graph/BFS){r}
  {g}[10]{r} Analytics dashboard    {y}(Sorted / Heap){r}
  {g}[11]{r} Process click queue    {y}(Queue flush){r}
  {g}[0]{r}  Exit
"""

def print_menu():
    print(MENU.format(
        bold=BOLD, cyan=CYAN, reset=RESET,
        g=GREEN, r=RESET, y=YELLOW
    ))

def input_prompt(prompt: str) -> str:
    return input(f"  {YELLOW}➜{RESET}  {prompt}: ").strip()

def do_shorten(store: URLStore):
    url = input_prompt("Enter URL to shorten")
    if not url:
        print(c("  ✖  No URL entered.", RED)); return
    try:
        short = store.shorten(url)
        print(c(f"\n  ✔  Shortened:  {short}", GREEN))
        print(f"     Stack depth now: {store.stack_depth()}")
    except ValueError as e:
        print(c(f"  ✖  {e}", RED))

def do_shorten_alias(store: URLStore):
    url   = input_prompt("Enter URL to shorten")
    alias = input_prompt("Enter custom alias (alphanumeric)")
    if not url or not alias:
        print(c("  ✖  URL and alias required.", RED)); return
    try:
        short = store.shorten(url, alias=alias)
        print(c(f"\n  ✔  Shortened:  {short}", GREEN))
    except ValueError as e:
        print(c(f"  ✖  {e}", RED))

def do_resolve(store: URLStore):
    code = input_prompt("Enter short link or code")
    ref  = input_prompt("Enter referrer (or press Enter for 'direct')")
    ref  = ref if ref else "direct"
    result = store.resolve(code, referrer=ref)
    if result:
        print(c(f"\n  ✔  Redirecting to: {result}", GREEN))
        print(f"     (Click event queued — queue depth: {store.queue_depth()})")
        webbrowser.open(result)
    else:
        print(c("  ✖  Short code not found.", RED))

def do_stats(store: URLStore):
    code = input_prompt("Enter short code or full short link")
    meta = store.stats(code)
    if not meta:
        print(c("  ✖  Not found.", RED)); return
    header(f"Stats: {meta['short_code']}")
    print(f"  Original  : {meta['original_url']}")
    print(f"  Alias     : {'Yes' if meta['alias'] else 'Auto-generated'}")
    print(f"  Clicks    : {c(meta['clicks'], YELLOW)}")
    print(f"  Created   : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(meta['created_at']))}")

def do_topk(store: URLStore, analytics: Analytics):
    k_str = input_prompt("How many top links? (default 5)")
    k = int(k_str) if k_str.isdigit() else 5
    store.process_click_queue()
    results = analytics.top_k_links(k)
    header(f"Top-{k} Most Clicked  [Heap O(n log k)]")
    if not results:
        print("  (no links yet)")
        return
    for i, r in enumerate(results, 1):
        print(f"  {i}. {c(r['short_code'], CYAN):20s}  clicks: {c(r['clicks'], YELLOW)}  → {r['original_url'][:50]}")

def do_undo(store: URLStore):
    msg = store.undo_last()
    if msg:
        print(c(f"\n  ✔  {msg}", GREEN))
        print(f"     Stack depth now: {store.stack_depth()}")
    else:
        print(c("  ✖  Nothing to undo (stack is empty).", RED))

def do_delete(store: URLStore):
    code = input_prompt("Enter short code to delete")
    if store.delete(code):
        print(c(f"  ✔  Deleted '{code}'.", GREEN))
    else:
        print(c("  ✖  Not found.", RED))

def do_search(store: URLStore):
    prefix = input_prompt("Enter code prefix to search")
    results = store.search_by_prefix(prefix)
    header(f"Binary Search Results for prefix '{prefix}'")
    if results:
        for code in results:
            meta = store.stats(code)
            print(f"  • {c(code, CYAN):20s} → {meta['original_url'][:60]}")
    else:
        print("  (no matches)")

def do_bfs(store: URLStore):
    ref = input_prompt("Enter referrer to start BFS from")
    codes = store.referrer_bfs(ref)
    header(f"BFS Referrer Graph from '{ref}'")
    if codes:
        for code in codes:
            print(f"  • {c(code, CYAN)}")
    else:
        print("  (no links reachable from this referrer)")

def do_dashboard(store: URLStore, analytics: Analytics):
    store.process_click_queue()
    dash = analytics.dashboard()
    header("Analytics Dashboard")
    print(f"  Total URLs    : {c(dash['total_urls'], YELLOW)}")
    print(f"  Total Clicks  : {c(dash['total_clicks'], YELLOW)}")
    print(f"  Queue Depth   : {dash['queue_depth']}")
    print(f"  Stack Depth   : {dash['stack_depth']}")
    print()
    print(f"  {BOLD}Top 3 Links:{RESET}")
    for i, r in enumerate(dash["top_3"], 1):
        print(f"    {i}. {c(r['short_code'], CYAN):20s}  {c(r['clicks'], YELLOW)} clicks")
    print()
    ref_breakdown = analytics.referrer_breakdown()
    if ref_breakdown:
        print(f"  {BOLD}Referrer Breakdown:{RESET}")
        for ref, count in list(ref_breakdown.items())[:5]:
            print(f"    {ref:20s}  → {count} link(s)")

def do_flush_queue(store: URLStore):
    n = store.process_click_queue()
    print(c(f"  ✔  Processed {n} click event(s) from queue.", GREEN))
    print(f"     Heap updated. Queue depth now: {store.queue_depth()}")

def seed_demo_data(store: URLStore):
    urls = [
        ("https://www.google.com",        "gl"),
        ("https://www.github.com",        "gh"),
        ("https://www.youtube.com",        "yt"),
        ("https://www.python.org",        "py"),
        ("https://www.instagram.com",        "ig"),

    ]
    referrers = ["twitter.com", "google.com", "direct", "email", "twitter.com"]
    for (url, alias), ref in zip(urls, referrers):
        code = store.shorten(url, alias=alias).replace(store.BASE_URL, "")
        for _ in range(len(url) % 7 + 1):
            store.resolve(code, referrer=ref)
    store.process_click_queue()
    print(c("  ✔  Demo data seeded (5 URLs with click history).", GREEN))

def main():
    store     = URLStore()
    analytics = Analytics(store)

    print(c("\n  Seeding demo data...", CYAN))
    seed_demo_data(store)

    while True:
        print_menu()
        choice = input_prompt("Choose option").strip()

        if   choice == "1":  do_shorten(store)
        elif choice == "2":  do_shorten_alias(store)
        elif choice == "3":  do_resolve(store)
        elif choice == "4":  do_stats(store)
        elif choice == "5":  do_topk(store, analytics)
        elif choice == "6":  do_undo(store)
        elif choice == "7":  do_delete(store)
        elif choice == "8":  do_search(store)
        elif choice == "9":  do_bfs(store)
        elif choice == "10": do_dashboard(store, analytics)
        elif choice == "11": do_flush_queue(store)
        elif choice == "0":
            print(c("\n  Goodbye!\n", CYAN))
            sys.exit(0)
        else:
            print(c("  ✖  Invalid option.", RED))

        input(f"\n  {YELLOW}Press Enter to continue...{RESET}")

if __name__ == "__main__":
    main()