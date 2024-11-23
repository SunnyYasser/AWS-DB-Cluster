from flask import Flask, jsonify, request
import requests
import mysql.connector
import os
import subprocess
import json

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
    
    print ("Read query :", query)

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
    
    print ("Write Query: ", query)

    with open('instance_details.json', 'r') as file:
         instance_details = json.load(file)
 
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        if instance['Name'] != 'mysql_master_node':
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])

    responses = []

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        affected_rows = cursor.rowcount
        connection.close()

        local_response = {
            "message": "Query executed successfully",
            "affected_rows": affected_rows
        }
    
    except mysql.connector.Error as err:
        local_response = {
            "message": "Query failed",
            "error": str(err),
            "affected_rows": 0
        }

    responses.append (local_response)

    for ip in public_ips:
        try:
            # Forward the query to the other servers
            url = f"http://{ip}:80/write"
            print ("Write replay URL: ", url)
            response = requests.post(url, json={"query": query})
            if response.status_code == 200:
                json_response = response.json()
                responses.append({
                    "message": json_response.get("message", "No message provided"),
                    "affected_rows": json_response.get("affected_rows", 0)
                })
            else:
                responses.append({
                    "message": "Query forwarding failed",
                    "error": response.json(),
                    "affected_rows": 0
                })
        except requests.RequestException as e:
            responses.append({
                "message": "Query forwarding failed",
                "error": str(e),
                "affected_rows": 0
            })

    return jsonify(responses), 200

if __name__ == "__main__":
    port = 80
    app.run(host="0.0.0.0", port=port)

