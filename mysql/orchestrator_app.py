# orchestrator_app.py
from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

# A list of worker IP addresses, passed during deployment
worker_ips = []

# Ports where each worker is running containers
ports = [5001, 5002]  # Assuming each worker runs two containers on different ports

@app.route('/process', methods=['POST'])
def process_request():
    # Randomly select a worker and port to handle the request
    worker_ip = random.choice(worker_ips)
    port = random.choice(ports)

    # Forward the request to the selected worker container
    worker_url = f"http://{worker_ip}:{port}/process"
    
    try:
        # Forward the request data to the worker container
        response = requests.post(worker_url, json=request.json)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': 'Failed to contact worker', 'details': str(e)}), 500

@app.route('/set_workers', methods=['POST'])
def set_workers():
    global worker_ips
    worker_ips = request.json.get('worker_ips', [])
    return jsonify({'status': 'Workers updated', 'worker_ips': worker_ips}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

