"""
Social microservice
"""

import sqlite3
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = Path(__file__).parent / "social.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS follows (
                follower_id TEXT NOT NULL,
                followee_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (follower_id, followee_id),
                CHECK (follower_id != followee_id)
            )
        """)
        conn.commit()
        

@app.route("/follows", methods=["POST"])
def create_follow():
    """Create a follow relationship. Body: { "follower_id": "...", "followee_id": "..." }"""
    data = request.get_json(force=True, silent=True) or {}
    follower_id = data.get("follower_id")
    followee_id = data.get("followee_id")

    if not follower_id or not followee_id:
        return jsonify({"error": "follower_id and followee_id are required"}), 400

    follower_id = str(follower_id).strip()
    followee_id = str(followee_id).strip()

    if follower_id == followee_id:
        return jsonify({"error": "Cannot follow yourself"}), 400

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO follows (follower_id, followee_id) VALUES (?, ?)",
                (follower_id, followee_id),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Already following this user"}), 409

    return jsonify({
        "follower_id": follower_id,
        "followee_id": followee_id,
        "message": "Follow relationship created",
    }), 201


@app.route("/follows", methods=["GET"])
def list_follows():
    """List follow relationships. Optional query: follower_id= or followee_id= to filter."""
    follower_id = request.args.get("follower_id")
    followee_id = request.args.get("followee_id")

    with get_db() as conn:
        if follower_id and followee_id:
            row = conn.execute(
                "SELECT follower_id, followee_id, created_at FROM follows WHERE follower_id = ? AND followee_id = ?",
                (follower_id, followee_id),
            ).fetchone()
            if not row:
                return jsonify({"follows": False}), 200
            return jsonify({
                "follows": True,
                "follower_id": row["follower_id"],
                "followee_id": row["followee_id"],
                "created_at": row["created_at"],
            }), 200

        query = "SELECT follower_id, followee_id, created_at FROM follows WHERE 1=1"
        params = []
        if follower_id:
            query += " AND follower_id = ?"
            params.append(follower_id)
        if followee_id:
            query += " AND followee_id = ?"
            params.append(followee_id)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()

    return jsonify({
        "follows": [
            {"follower_id": r["follower_id"], "followee_id": r["followee_id"], "created_at": r["created_at"]}
            for r in rows
        ]
    }), 200


@app.route("/users/<follower_id>/following/<followee_id>", methods=["DELETE"])
def delete_follow(follower_id, followee_id):
    """Remove a follow relationship (unfollow)."""
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM follows WHERE follower_id = ? AND followee_id = ?",
            (follower_id, followee_id),
        )
        deleted = cur.rowcount
        conn.commit()
    if deleted == 0:
        return jsonify({"error": "Follow relationship not found"}), 404
    return jsonify({"message": "Unfollowed"}), 200


@app.route("/users/<user_id>/following", methods=["GET"])
def list_following(user_id):
    """List users that this user follows."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT followee_id, created_at FROM follows WHERE follower_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return jsonify({
        "user_id": user_id,
        "following": [r["followee_id"] for r in rows],
    }), 200


@app.route("/users/<user_id>/followers", methods=["GET"])
def list_followers(user_id):
    """List users who follow this user."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT follower_id, created_at FROM follows WHERE followee_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return jsonify({
        "user_id": user_id,
        "followers": [r["follower_id"] for r in rows],
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)
