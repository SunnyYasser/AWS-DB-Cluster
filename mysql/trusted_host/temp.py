from flask import Flask, jsonify, request
import re
import requests
import json

app = Flask(__name__)

# Allowed query modes
ALLOWED_MODES = {"DIRECT", "RANDOM", "CUSTOMIZED"}

# Dummy credentials for demonstration
VALID_CREDENTIALS = {
    "sysbench_user": "sysbench_password"
}

# Health Check Endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


# Process Query Endpoint
@app.route("/process", methods=["POST"])
def process_query():
    data = request.json
    
    print(data)

    # Validate request payload keys
    if "query" not in data or "mode" not in data:
        return jsonify({"error": "Missing required keys. Required keys: 'query', 'mode'"}), 400

    mode = data.get("mode").upper()

    # Validate mode
    if mode not in ALLOWED_MODES:
        return jsonify({"error": f"Invalid mode. Allowed modes are: {', '.join(ALLOWED_MODES)}"}), 400

    print (request.headers)

    # Authenticate using headers
    username = request.headers.get("username")
    password = request.headers.get("password")

    print (f"{username} : {password}")

    if not username or not password:
        return jsonify({"error": "Missing 'username' or 'password' in headers."}), 401

    if username not in VALID_CREDENTIALS or VALID_CREDENTIALS[username] != password:
        return jsonify({"error": "Invalid username or password."}), 403
    
    # If all checks pass, process the query
    with open('proxy_manager_details.json', 'r') as file:
         instance_details = json.load(file)
    
    proxy_manager_ip = None
    for instance in instance_details:
        proxy_manager_ip = instance['PublicIP']

    url = f"http://{proxy_manager_ip}:80/process"
    
    print (url)

    response = None
    try:
        # All requests are forwarded as POST
        resp = requests.post(url, json=data)

        # Check if the response is successful
        if resp.status_code == 200:
            response = resp.json()
        else:
            response = {
                "message": "Query execution failed",
                "error": resp.text,
                "affected_rows": 0
            }
    except requests.RequestException as e:
        # Handle request exceptions
        response = {
            "message": "Query forwarding failed",
            "error": str(e),
            "affected_rows": 0
        }

    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

