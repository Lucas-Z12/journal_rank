import os
import sys
import threading
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Reuse existing algorithm.py but override DATA_DIR for deployment.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import algorithm as ranking_algorithm  # noqa: E402

DEFAULT_DATA_DIR = PROJECT_ROOT / "Transition_matrix"
ranking_algorithm.DATA_DIR = Path(os.environ.get("DATA_DIR", str(DEFAULT_DATA_DIR)))

FIELD_MAP = ranking_algorithm.FIELD_MAP
main = ranking_algorithm.main

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
CACHE_TTL_SECONDS = int(os.environ.get("API_CACHE_TTL_SECONDS", "900"))
CACHE_MAX_ENTRIES = int(os.environ.get("API_CACHE_MAX_ENTRIES", "128"))
_RESPONSE_CACHE = OrderedDict()
_CACHE_LOCK = threading.Lock()


def _cache_key(start_year, end_year, field):
    if field is None:
        normalized_field = ("all",)
    elif isinstance(field, list):
        normalized_field = tuple(sorted(set(field)))
    else:
        normalized_field = (field,)
    return start_year, end_year, normalized_field


def _get_cached_response(key):
    now = time.time()
    with _CACHE_LOCK:
        item = _RESPONSE_CACHE.get(key)
        if item is None:
            return None
        ts, payload = item
        if now - ts > CACHE_TTL_SECONDS:
            _RESPONSE_CACHE.pop(key, None)
            return None
        # Move to end to keep LRU-like behavior.
        _RESPONSE_CACHE.move_to_end(key)
        return payload


def _set_cached_response(key, payload):
    with _CACHE_LOCK:
        _RESPONSE_CACHE[key] = (time.time(), payload)
        _RESPONSE_CACHE.move_to_end(key)
        while len(_RESPONSE_CACHE) > CACHE_MAX_ENTRIES:
            _RESPONSE_CACHE.popitem(last=False)


def load_index_html() -> str:
    index_path = PROJECT_ROOT / "index.html"
    html = index_path.read_text(encoding="utf-8")
    # Use same-origin API path in deployment.
    return html.replace(
        'const API_BASE = "http://127.0.0.1:5000";',
        'const API_BASE = "";'
    )


@app.route("/")
def index() -> Response:
    return Response(load_index_html(), mimetype="text/html")


@app.route("/api/test", methods=["GET"])
def test_api():
    return jsonify(
        {
            "status": "ok",
            "message": "API service is running",
            "timestamp": time.time(),
            "version": "deploy-render-1.0.0",
            "fields": list(FIELD_MAP.keys()),
            "data_dir": str(ranking_algorithm.DATA_DIR),
        }
    )


@app.route("/api/generate-rankings", methods=["POST"])
def generate_rankings():
    try:
        data = request.get_json(silent=True) or {}
        start_year = int(data.get("start_year", 2013))
        end_year = int(data.get("end_year", 2015))
        field = data.get("field", "economics")

        if field == "all":
            field = None
        elif isinstance(field, list):
            if "all" in field:
                field = None
            else:
                invalid_fields = [f for f in field if f not in FIELD_MAP]
                if invalid_fields:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f"field参数不合法，可选: all, {', '.join(FIELD_MAP.keys())}",
                            }
                        ),
                        400,
                    )
                if not field:
                    field = None

        if start_year > end_year:
            start_year, end_year = end_year, start_year

        if field is not None and not isinstance(field, list) and field not in FIELD_MAP:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"field参数不合法，可选: all, {', '.join(FIELD_MAP.keys())}",
                    }
                ),
                400,
            )

        period = str(start_year) if start_year == end_year else f"{start_year}-{end_year}"
        request_key = _cache_key(start_year, end_year, field)
        cached_payload = _get_cached_response(request_key)
        if cached_payload is not None:
            return jsonify(cached_payload)

        start_time = time.time()

        df, invalid_items, fallback_mode = main(
            start_year=start_year,
            end_year=end_year,
            field=field,
        )

        execution_time = round((time.time() - start_time) * 1000, 2)
        metrics = {
            "period": period,
            "field": field or "all",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_rows": len(df),
            "fallback_mode": fallback_mode,
            "invalid_count": len(invalid_items),
        }

        response = {
            "success": True,
            "period": period,
            "start_year": start_year,
            "end_year": end_year,
            "field": field or "all",
            "execution_time": execution_time,
            "columns": list(df.columns),
            "data": df.to_dict("records"),
            "invalid_items": invalid_items,
            "metrics": metrics,
        }
        _set_cached_response(request_key, response)
        return jsonify(response)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=False)
