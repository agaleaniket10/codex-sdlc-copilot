"""
Legacy Flask application — intentionally uses outdated patterns.
Used as the sample input for both test-gen and migration-assist modes.
"""

import hashlib
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = "users.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


@app.route("/users", methods=["GET"])
def get_users():
    conn = get_db()
    cursor = conn.execute("SELECT id, username, email FROM users")
    users = [
        {"id": row[0], "username": row[1], "email": row[2]} for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(users)


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db()
    cursor = conn.execute(
        "SELECT id, username, email FROM users WHERE id = ?", (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": row[0], "username": row[1], "email": row[2]})


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data["username"]
    email = data["email"]
    password = hashlib.md5(data["password"].encode()).hexdigest()  # insecure hash

    conn = get_db()
    # Vulnerable to SQL injection if not using parameterised queries
    conn.execute(
        f"INSERT INTO users (username, email, password) VALUES ('{username}', '{email}', '{password}')"
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "created"}), 201


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "deleted"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = hashlib.md5(data["password"].encode()).hexdigest()

    conn = get_db()
    cursor = conn.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?", (username, password)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"token": f"fake-token-{row[0]}"})
    return jsonify({"error": "invalid credentials"}), 401


def calculate_discount(price, discount_percent):
    """Calculate discounted price. No input validation."""
    return price - (price * discount_percent / 100)


def parse_csv_line(line):
    """Parse a comma-separated line into a list of values."""
    return line.strip().split(",")


def format_user_display(user_dict):
    """Format user data for display."""
    return f"{user_dict['username']} <{user_dict['email']}>"


if __name__ == "__main__":
    app.run(debug=True)
