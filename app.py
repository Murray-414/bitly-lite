

import sys
import os
import time
import webbrowser
import threading

from flask import Flask, request, jsonify, redirect, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.url_store import URLStore
from src.analytics import Analytics

app = Flask(__name__, static_folder="ui", static_url_path="")

store = URLStore()
analytics = Analytics(store)

def seed():
    demos = [
        ("https://www.google.com",        "gl"),
        ("https://www.github.com",        "gh"),
        ("https://www.youtube.com",        "yt"),
        ("https://www.python.org",        "py"),
       ("https://www.instagram.com",        "ig"),
    ]
    refs = ["google.com", "twitter.com", "direct", "email", "reddit.com"]
    for (url, alias), ref in zip(demos, refs):
        code = store.shorten(url, alias=alias).replace(store.BASE_URL, "")
        for _ in range(len(url) % 6 + 1):
            store.resolve(code, referrer=ref)
    store.process_click_queue()

seed()

@app.route("/")
def index():
    return send_from_directory("ui", "index.html")

@app.route("/api/shorten", methods=["POST"])
def api_shorten():
    data = request.get_json()
    url = (data.get("url") or "").strip()
    alias = (data.get("alias") or "").strip() or None
    if not url:
        return jsonify({"error": "URL is required"}), 400
    if not url.startswith("http"):
        url = "https://" + url
    try:
        short = store.shorten(url, alias=alias)
        meta = store.stats(short.replace(store.BASE_URL, ""))
        return jsonify({
            "short": short,
            "code": short.replace(store.BASE_URL, ""),
            "original": url,
            "clicks": meta["clicks"],
            "alias": meta["alias"],
            "created": time.strftime("%Y-%m-%d %H:%M", time.localtime(meta["created_at"]))
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 409

@app.route("/r/<code>")
def api_resolve(code):
    referrer = request.referrer or "direct"
    original = store.resolve(code, referrer=referrer)
    store.process_click_queue()
    if original:
        return redirect(original)
    return jsonify({"error": "Short code not found"}), 404

@app.route("/api/urls")
def api_urls():
    store.process_click_queue()
    urls = store.all_sorted_by_clicks()
    result = []
    for u in urls:
        result.append({
            "code": u["short_code"],
            "short": store.BASE_URL + u["short_code"],
            "original": u["original_url"],
            "clicks": u["clicks"],
            "alias": u["alias"],
            "created": time.strftime("%Y-%m-%d %H:%M", time.localtime(u["created_at"]))
        })
    return jsonify(result)

@app.route("/api/topk")
def api_topk():
    k = int(request.args.get("k", 5))
    store.process_click_queue()
    results = analytics.top_k_links(k)
    return jsonify([{
        "code": r["short_code"],
        "original": r["original_url"],
        "clicks": r["clicks"]
    } for r in results])

@app.route("/api/stats/<code>")
def api_stats(code):
    meta = store.stats(code)
    if not meta:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "code": meta["short_code"],
        "original": meta["original_url"],
        "clicks": meta["clicks"],
        "alias": meta["alias"],
        "created": time.strftime("%Y-%m-%d %H:%M", time.localtime(meta["created_at"]))
    })

@app.route("/api/undo", methods=["POST"])
def api_undo():
    msg = store.undo_last()
    if msg:
        return jsonify({"message": msg})
    return jsonify({"error": "Nothing to undo"}), 400

@app.route("/api/delete/<code>", methods=["DELETE"])
def api_delete(code):
    if store.delete(code):
        return jsonify({"message": f"Deleted '{code}'"})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/dashboard")
def api_dashboard():
    store.process_click_queue()
    dash = analytics.dashboard()
    return jsonify({
        "total_urls": dash["total_urls"],
        "total_clicks": dash["total_clicks"],
        "queue_depth": dash["queue_depth"],
        "stack_depth": dash["stack_depth"],
        "top3": [{
            "code": r["short_code"],
            "original": r["original_url"],
            "clicks": r["clicks"]
        } for r in dash["top_3"]]
    })

@app.route("/api/search")
def api_search():
    prefix = request.args.get("q", "")
    codes = store.search_by_prefix(prefix)
    results = []
    for code in codes:
        meta = store.stats(code)
        if meta:
            results.append({
                "code": code,
                "original": meta["original_url"],
                "clicks": meta["clicks"]
            })
    return jsonify(results)

if __name__ == "__main__":
    def open_browser():
        time.sleep(1)
        webbrowser.open("http://127.0.0.1:5000")
    threading.Thread(target=open_browser, daemon=True).start()
    print("\n  🔗  Bitly-Lite running at http://127.0.0.1:5000\n")
    app.run(debug=False, port=5000)