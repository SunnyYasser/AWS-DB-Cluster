from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "sysbench_user",
    "password": "sysbench_password",
    "database": "sakila",
}

# Health Check Endpoint
@app.route("/health", methods=["GET"])
def health_check():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            connection.close()
            return jsonify({"status": "healthy"}), 200
    except mysql.connector.Error as err:
        return jsonify({"status": "unhealthy", "error": str(err)}), 500

# Execute a Read Query Endpoint
@app.route("/read", methods=["POST"])
def read_data():
    data = request.json
    query = data.get("query")

    if not query:
        return jsonify({"error": "Query string is required"}), 400

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        connection.close()
        return jsonify({"data": rows}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

# Execute a Write Query Endpoint
@app.route("/write", methods=["POST"])
def write_data():
    data = request.json
    query = data.get("query")

    if not query:
        return jsonify({"error": "Query string is required"}), 400

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        affected_rows = cursor.rowcount
        connection.close()
        return jsonify({"message": "Query executed successfully", "affected_rows": affected_rows}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

if __name__ == "__main__":
    port = 5001
    app.run(host="0.0.0.0", port=port)

