import json
import requests
import time
from statistics import mean, stdev

# Authentication credentials
USERNAME = "sysbench_user"
PASSWORD = "sysbench_password"

# Function to generate unique INSERT and UPDATE queries
def generate_queries():
    queries = {
        "INSERT": [
            f"INSERT INTO actor (first_name, last_name, last_update) VALUES ('Actor{i}', 'Lastname{i}', NOW());"
            for i in range(100)
        ],
        "UPDATE": [
            f"UPDATE actor SET last_name = 'UpdatedLastname{i}' WHERE first_name = 'Actor{i}';"
            for i in range(100)
        ],
        "SELECT": [
            f"SELECT * FROM actor WHERE actor_id = {i};" for i in range(100)
        ],
    }
    return queries

# Function to make a request to the Flask app
def make_request(query, mode, repetitions):
    with open('gatekeeper_details.json', 'r') as file:
        instance_details = json.load(file)

    public_ips = [instance['PublicIP'] for instance in instance_details]

    # Base URL of the Flask app
    BASE_URL = f"http://{public_ips[0]}:80/process"

    headers = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response_times = []

    for _ in range(repetitions):
        for q in query:
            print (q)
            payload = {"query": q, "mode": mode}
            try:
                start_time = time.time()
                response = requests.post(BASE_URL, json=payload, headers=headers)
                end_time = time.time()
                response_times.append(end_time - start_time)

                if response.status_code != 200:
                    print(f"Error ({mode}):", response.status_code, response.json())
                else:
                    print (response.json())
            except requests.RequestException as e:
                print(f"Request failed ({mode}):", e)

    # Calculate statistics
    avg_time = mean(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    std_dev = stdev(response_times) if len(response_times) > 1 else 0

    print(f"\nStatistics for {mode} mode:")
    print(f"  Total requests: {len(query) * repetitions}")
    print(f"  Average time: {avg_time:.4f} seconds")
    print(f"  Min time: {min_time:.4f} seconds")
    print(f"  Max time: {max_time:.4f} seconds")
    print(f"  Std deviation: {std_dev:.4f} seconds\n")

if __name__ == "__main__":
    repetitions = 10
    queries = generate_queries()

    # Run queries in RANDOM mode
    print("Running SELECT queries in RANDOM mode...")
    make_request(queries["SELECT"], "RANDOM", repetitions)

    # Run queries in CUSTOMIZED mode
    print("Running SELECT queries in CUSTOMIZED mode...")
    make_request(queries["SELECT"], "CUSTOMIZED", repetitions)

    # Run queries in DIRECT mode (mix of INSERT and UPDATE)
    print("Running mixed INSERT and UPDATE queries in DIRECT mode...")
    make_request(queries["INSERT"] + queries["UPDATE"], "DIRECT", repetitions)

