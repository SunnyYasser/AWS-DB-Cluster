import json
import requests

# Authentication credentials
USERNAME = "sysbench_user"
PASSWORD = "sysbench_password"

# Example queries for the Sakila database
QUERIES = {
    "SELECT": "SELECT * FROM actor;",
    "INSERT": "INSERT INTO actor (first_name, last_name, last_update) VALUES ('John', 'Doe', NOW());",
    "UPDATE": "UPDATE actor SET last_name = 'Smith' WHERE first_name = 'John';"
}

# Function to make a request to the Flask app
def make_request(query, mode):
    
    with open('gatekeeper_details.json', 'r') as file:
         instance_details = json.load(file)
    
    instance_ids = []
    public_ips = []
    for instance in instance_details:
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])
    
    # Base URL of the Flask app
    BASE_URL = f"http://{public_ips[0]}:80/process"

    headers = {
        "username": USERNAME,
        "password": PASSWORD
    }
    payload = {
        "query": query,
        "mode": mode
    }
    try:
        response = requests.post(BASE_URL, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Success ({mode}):", response.json())
        else:
            print(f"Error ({mode}):", response.status_code, response.json())
    except requests.RequestException as e:
        print(f"Request failed ({mode}):", e)


if __name__ == "__main__":
    # Example: Run a SELECT query in RANDOM mode
    make_request(QUERIES["SELECT"], "RANDOM")

    # Example: Run an INSERT query in DIRECT mode
    make_request(QUERIES["INSERT"], "DIRECT")

    # Example: Run an UPDATE query in DIRECT mode
    make_request(QUERIES["UPDATE"], "DIRECT")

    # Example: Run a SELECT query in CUSTOMIZED mode
    make_request(QUERIES["SELECT"], "CUSTOMIZED")
