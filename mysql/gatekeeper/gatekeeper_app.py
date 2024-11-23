from flask import Flask, jsonify, request
import re
import requests
import json

app = Flask(__name__)

# Regular expression for basic SQL injection prevention
SQL_SANITIZATION_REGEX = re.compile(r"^[a-zA-Z0-9\s,.*_=<>@'\"()-]+;?$")

# Health Check Endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Process Query Endpoint
@app.route("/process", methods=["POST"])
def process_query():
    data = request.json

    query = data.get("query")

    # Check if query is sanitized
    if not SQL_SANITIZATION_REGEX.match(query.strip()):
        return jsonify({"error": "Query contains potentially dangerous characters or is not sanitized."}), 400

    # If all checks pass, process the query
    with open('trusted_host_details.json', 'r') as file:
         instance_details = json.load(file)
    
    trusted_host_ip = None
    for instance in instance_details:
        trusted_host_ip = instance['PublicIP']

    url = f"http://{trusted_host_ip}:80/process"

    response = None
    try:
        # All requests are forwarded as POST
        resp = requests.post(url, json=data, headers=request.headers)

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


