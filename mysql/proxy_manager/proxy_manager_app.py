from flask import Flask, jsonify, request
import requests
import os
import subprocess
import json
import random

app = Flask(__name__)

def ping_ip(ip):
    """
    Pings an IP address and returns the average ping time in milliseconds.
    Returns None if the ping fails.
    """
    command = ['ping', '-c', '1', ip]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Extract the average ping time from the ping output
            output = result.stdout
            time_line = next(line for line in output.splitlines() if "time=" in line)
            time_ms = float(time_line.split("time=")[1].split()[0])
            return time_ms
        else:
            return None
    except Exception as e:
        return None


def find_instance_with_lowest_ping():
    """
    Finds the instance ID and IP with the lowest ping.
    """
    
    with open('instance_details.json', 'r') as file:
         instance_details = json.load(file)
 
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        if instance['Name'] != 'mysql_master_node':
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])


    lowest_ping = float('inf')
    best_instance_id = None
    best_ip = None

    for instance_id, ip in zip(instance_ids, public_ips):
        ping_time = ping_ip(ip)
        if ping_time is not None and ping_time < lowest_ping:
            lowest_ping = ping_time
            best_instance_id = instance_id
            best_ip = ip
    
    return best_instance_id, best_ip

def find_random_read_node ():
    """
    Finds random read node IP
    """
    
    with open('instance_details.json', 'r') as file:
         instance_details = json.load(file)
 
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        if instance['Name'] != 'mysql_master_node':
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])

    random_index = random.randint(0, len(instance_ids) - 1)
    
    # Get the instance ID and public IP at the random index
    random_instance_id = instance_ids[random_index]
    random_ip = public_ips[random_index]
    
    return random_instance_id, random_ip


def get_master_node_ip():
    """
    Finds master write node IP
    """
    
    with open('instance_details.json', 'r') as file:
         instance_details = json.load(file)
 
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        if instance['Name'] == 'mysql_master_node':
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])

    return instance_ids[0], public_ips[0]


def make_call(url, payload):
    print ("URL to redirect: ", url)
    print ("Payload: ", payload)
    response = None
    try:
        # All requests are forwarded as POST
        resp = requests.post(url, json=payload)

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

@app.route("/process", methods=["POST"])
def process_query():
    data = request.json
    query = data.get("query")
    mode = data.get("mode")
    url = None

    try:
        # Mode-based routing logic
        if mode == "DIRECT":
            _, master_ip = get_master_node_ip()
            url = f"http://{master_ip}:80/write"  # All queries go to write endpoint
        elif mode == "RANDOM":
            _, random_ip = find_random_read_node()
            url = f"http://{random_ip}:80/read"
        else:    
            _, lowest_ping_ip = find_instance_with_lowest_ping()
            url = f"http://{lowest_ping_ip}:80/read"
        
        # Make the API call and return the response
        return jsonify(make_call(url, {"query": query})), 200

    except Exception as e:
        # General exception handling
        return jsonify({"error": str(e)}), 500
    

# Health Check Endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = 80
    app.run(host="0.0.0.0", port=port)

