"""
Memory API  –  adds retrieval (semantic search) & simple health/debug endpoints.
Place in: server/routes/memory_api.py
"""

from flask import Blueprint, request, jsonify
from server.models.memory_store import MemoryStore

memory_bp = Blueprint("memory", __name__)
memory = MemoryStore()


@memory_bp.route("/memory/add", methods=["POST"])
def add_memory():
    data = request.get_json(force=True)
    if not data or "content" not in data:
        return jsonify({"error": "Missing content field"}), 400

    ok = memory.add_memory(
        data.get("session_id", "unknown"),
        data.get("user_id", "anonymous"),
        data["content"],
        data.get("source_type", "transcript"),
    )

    if ok:
        return jsonify({"status": "ok", "message": "Memory stored successfully."})
    return jsonify({"status": "error", "message": "Failed to store memory."}), 500


@memory_bp.route("/memory/search", methods=["GET", "POST"])
def search_memory():
    if request.method == "GET":
        query = request.args.get("query")
        top_k = int(request.args.get("top_k", 5))
    else:
        data = request.get_json(force=True)
        query = data.get("query")
        top_k = int(data.get("top_k", 5))

    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    results = memory.search_memory(query, top_k)
    return jsonify({"query": query, "results": results}), 200


@memory_bp.route("/memory/debug", methods=["GET"])
def debug_memory():
    """Return a few recent rows for quick inspection."""
    try:
        rows = memory.search_memory("", top_k=10)
        return jsonify({"latest": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500