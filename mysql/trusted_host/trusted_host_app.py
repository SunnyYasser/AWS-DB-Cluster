from flask import Flask, jsonify, request
import logging
import re
import requests
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set log level to DEBUG to capture all logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Log messages to a file
        logging.StreamHandler()          # Log messages to the console
    ]
)

# Allowed query modes
ALLOWED_MODES = {"DIRECT", "RANDOM", "CUSTOMIZED"}

# Dummy credentials for demonstration
VALID_CREDENTIALS = {
    "sysbench_user": "sysbench_password"
}

@app.route("/health", methods=["GET"])
def health_check():
    app.logger.info("Health check endpoint accessed")
    return jsonify({"status": "healthy"}), 200

@app.route("/process", methods=["POST"])
def process_query():
    data = request.json

    app.logger.debug(f"Received request payload: {data}")

    # Validate request payload keys
    if "query" not in data or "mode" not in data:
        app.logger.warning("Missing required keys in request payload")
        return jsonify({"error": "Missing required keys. Required keys: 'query', 'mode'"}), 400

    mode = data.get("mode").upper()

    # Validate mode
    if mode not in ALLOWED_MODES:
        app.logger.warning(f"Invalid mode provided: {mode}")
        return jsonify({"error": f"Invalid mode. Allowed modes are: {', '.join(ALLOWED_MODES)}"}), 400

    # Authenticate using headers
    username = request.headers.get("username")
    password = request.headers.get("password")

    app.logger.debug(f"Authentication attempt by username: {username}")

    if not username or not password:
        app.logger.error("Authentication failed: Missing credentials")
        return jsonify({"error": "Missing 'username' or 'password' in headers."}), 401

    if username not in VALID_CREDENTIALS or VALID_CREDENTIALS[username] != password:
        app.logger.error("Authentication failed: Invalid username or password")
        return jsonify({"error": "Invalid username or password."}), 403

    # If all checks pass, process the query
    try:
        with open('proxy_manager_details.json', 'r') as file:
            instance_details = json.load(file)
        
        proxy_manager_ip = None
        for instance in instance_details:
            proxy_manager_ip = instance['PublicIP']

        url = f"http://{proxy_manager_ip}:80/process"
        app.logger.info(f"Forwarding request to proxy manager at {url}")

        # Forward the request
        resp = requests.post(url, json=data)

        # Check if the response is successful
        if resp.status_code == 200:
            app.logger.info("Query processed successfully by proxy manager")
            return resp.json()
        else:
            app.logger.error(f"Query execution failed: {resp.text}")
            return jsonify({
                "message": "Query execution failed",
                "error": resp.text,
                "affected_rows": 0
            })
    except requests.RequestException as e:
        app.logger.critical(f"Query forwarding failed: {str(e)}")
        return jsonify({
            "message": "Query forwarding failed",
            "error": str(e),
            "affected_rows": 0
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

