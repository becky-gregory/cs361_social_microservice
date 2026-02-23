"""Given an activity exists that I have not yet interacted with, when I send a request to its 
like endpoint, then the system should record my engagement."""

import sqlite3
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = Path(__file__).parent / "social.db"

# TESTING - Hardcoded activities for validating, can be deleted in future.
#activities = {
#    1: {"id": 1, "author": 2, "summary": "Ran 10 miles"},
#    2: {"id": 2, "author": 2, "summary": "Lifted weights"},
#}

likes_by_activity ={}

# --- POST LIKES ---
@app.post("/activity_likes")
def like_activity():
    data = request.get_json()
    user_id = data.get("user_id")
    activity_id = data.get("activity_id")

    if not isinstance(user_id, str) or user_id.strip() == "":
        return jsonify({"error": "user_id is required."}), 404

    if not isinstance(activity_id, int):
        return jsonify({"error": "activity_id (integer) is required"}), 404

    if activity_id not in likes_by_activity:
        likes_by_activity[activity_id] = set()
    likes_by_activity[activity_id].add(user_id)
    total_likes = likes_by_activity[activity_id]

    return jsonify({
    "activity_id": activity_id,
    "like_count": len(total_likes),
    "is_liked_by": user_id in total_likes
  }
), 200


# --- GET LIKES ---
@app.get("/activities/<int:activity_id>/likes")
def list_activity_likes(activity_id):
    total_likes = likes_by_activity.get(activity_id, set())
    return jsonify({
        "activity_id": activity_id,
        "like_count": len(total_likes),
        "likes": sorted(total_likes)
    }
)


# --- DELETE LIKES ---
@app.delete("/activities/<int:activity_id>/likes/<user_id>")
def unlike_activity(activity_id, user_id):
    user_id = str(user_id).strip()
    if user_id == "":
        return jsonify({"error": "user_id is required"})

    if not isinstance(activity_id, int):
        return jsonify({"error": "activity_id(int) is invalid"}), 400

    
    if activity_id in likes_by_activity:
        likes_by_activity[activity_id].discard(user_id)
        if not likes_by_activity[activity_id]:
            del likes_by_activity[activity_id]

    total_likes = likes_by_activity.get(activity_id, set())
    return jsonify({
        "activity_id": activity_id,
        "like_count": len(total_likes),
        "is_liked_by": user_id in total_likes
    }
), 200

if __name__ == "__main__":
  app.run(host="127.0.0.1", port=8000, debug=True)

