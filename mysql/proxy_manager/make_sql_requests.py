import requests
import json

# Flask App URL
BASE_URL = "http://localhost:80"

# Health Check Request
def health_check():
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("Health check passed:", response.json())
    else:
        print("Health check failed:", response.json())

# Read Data Request
def read_data(query):
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    response = requests.post(f"{BASE_URL}/read", headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print("Read Data Response:", response.json())
    else:
        print("Error reading data:", response.json())

# Write Data Request
def write_data(query):
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    response = requests.post(f"{BASE_URL}/write", headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        print("Write Data Response:", response.json())
    else:
        print("Error writing data:", response.json())

# Main Execution
if __name__ == "__main__":
    # Perform health check
    health_check()

    # Example of read data query (e.g., SELECT query)
    read_query = "SELECT * FROM actor LIMIT 5;"
    read_data(read_query)

    # Example of write data query (e.g., INSERT query)
    write_query = "INSERT INTO actor (first_name, last_name, last_update) VALUES ('Bruce', 'Wayne', NOW());"
    write_data(write_query)

