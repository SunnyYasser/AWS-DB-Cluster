from flask import Flask, jsonify, request
import re
import requests
import json
import logging

app = Flask(__name__)

# Configure logging to capture all levels, including DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
#logger = logging.getLogger(__name__)

# Regular expression for basic SQL injection prevention
SQL_SANITIZATION_REGEX = re.compile(r"^[a-zA-Z0-9\s,.*_=<>@'\"()-]+;?$")

# Health Check Endpoint
@app.route("/health", methods=["GET"])
def health_check():
    app.logger.info("Health check endpoint accessed")
    return jsonify({"status": "healthy"}), 200

# Process Query Endpoint
@app.route("/process", methods=["POST"])
def process_query():
    app.logger.info("Processing query endpoint accessed")
    data = request.json

    query = data.get("query")
    app.logger.debug(f"Received query: {query}")

    # Check if query is sanitized
    if not query or not SQL_SANITIZATION_REGEX.match(query.strip()):
        app.logger.warning("Query failed sanitization check")
        return jsonify({"error": "Query contains potentially dangerous characters or is not sanitized."}), 400

    # If all checks pass, process the query
    try:
        with open('trusted_host_details.json', 'r') as file:
            instance_details = json.load(file)
        
        trusted_host_ip = None
        for instance in instance_details:
            trusted_host_ip = instance['PublicIP']
        
        if not trusted_host_ip:
            app.logger.error("No trusted host IP found in the configuration")
            return jsonify({"error": "No trusted host found"}), 500

        app.logger.info(f"Forwarding request to trusted host: {trusted_host_ip}")
        url = f"http://{trusted_host_ip}:80/process"

        # Forward the request
        resp = requests.post(url, json=data, headers=request.headers)

        if resp.status_code == 200:
            app.logger.info("Query forwarded successfully")
            return resp.json()
        else:
            app.logger.error(f"Query forwarding failed with status code: {resp.status_code}")
            return jsonify({
                "message": "Query execution failed",
                "error": resp.text,
                "affected_rows": 0
            }), resp.status_code

    except requests.RequestException as e:
        app.logger.error(f"Request exception occurred: {e}")
        return jsonify({
            "message": "Query forwarding failed",
            "error": str(e),
            "affected_rows": 0
        }), 500

if __name__ == "__main__":
    app.logger.info("Starting Flask application")
    app.run(host="0.0.0.0", port=80)

