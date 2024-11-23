import requests
import json

# Flask App URL
BASE_URL = "http://3.87.87.79:80"

# Health Check Request
def health_check():
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("Health check passed:", response.json())
    else:
        print("Health check failed:", response.json())

#Process Data Request
def process_query(query):
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    response = requests.post(f"{BASE_URL}/process", headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print("Data Response:", response.json())
    else:
        print("Error: ", response.json())


# Main Execution
if __name__ == "__main__":
    # Perform health check
    health_check()

    read_query = "SELECT * FROM actor;"
    write_query = "INSERT INTO actor (first_name, last_name, last_update) VALUES ('Bruce', 'Wayne', NOW());"
    write_query2 = "DELETE FROM actor WHERE first_name = 'Bruce';"
    
    process_query(write_query)
    process_query(read_query)
    process_query(write_query2)
    process_query(read_query)
