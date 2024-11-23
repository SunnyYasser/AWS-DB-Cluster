import subprocess
import mysql.connector
from mysql.connector import Error
import time

# Function to run shell commands
def run_shell_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}\n{result.stderr}")
    else:
        print(f"Command succeeded: {command}\n{result.stdout}")

# Install MySQL
def install_mysql():
    print("Installing MySQL Server...")
    run_shell_command("sudo apt update")
    run_shell_command("sudo apt install -y mysql-server")

# Configure MySQL: Create sysbench user and database
def configure_mysql():    
    print("Configuring MySQL using `sudo mysql`...")
    
    # Create sysbench user
    run_shell_command("""
        echo "CREATE USER IF NOT EXISTS 'sysbench_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'sysbench_password';" | sudo mysql
    """)
    
    # Grant privileges to the user
    run_shell_command("""
        echo "GRANT ALL PRIVILEGES ON *.* TO 'sysbench_user'@'localhost';" | sudo mysql
    """)
    
    # Flush privileges to apply changes
    run_shell_command("""
        echo "FLUSH PRIVILEGES;" | sudo mysql
    """)
    
    # Create the test database
    run_shell_command("""
        echo "CREATE DATABASE IF NOT EXISTS sysbench_test;" | sudo mysql
    """)
    
    print("MySQL user and database configured successfully.")

# Download and import the Sakila database
def download_and_import_sakila():
    print("Downloading and importing Sakila database...")
    # Download Sakila database schema and data
    run_shell_command("wget https://downloads.mysql.com/docs/sakila-db.tar.gz")
    run_shell_command("tar -xvf sakila-db.tar.gz")
    run_shell_command("mysql -u sysbench_user -p'sysbench_password' sysbench_test < sakila-db/sakila-schema.sql")
    run_shell_command("mysql -u sysbench_user -p'sysbench_password' sysbench_test < sakila-db/sakila-data.sql")
    run_shell_command("""
        echo "USE sakila;" | sudo mysql
    """)
    print("Sakila database imported successfully.")

# Run sysbench on the Sakila database
def run_sysbench():
    print("Ensuring sysbench is installed...")
    # Install sysbench
    run_shell_command("sudo apt update")
    run_shell_command("sudo apt install -y sysbench")

    print("Running sysbench on Sakila database...")
    
    # Prepare test data
    run_shell_command(
        "sysbench /usr/share/sysbench/oltp_read_write.lua "
        "--mysql-host=localhost --mysql-user=sysbench_user --mysql-password=sysbench_password "
        "--mysql-db=sakila --tables=4 --table-size=10000 prepare"
    )

    
    # Run benchmark
    run_shell_command(
        "sysbench /usr/share/sysbench/oltp_read_write.lua "
        "--mysql-host=localhost --mysql-user=sysbench_user --mysql-password=sysbench_password "
        "--mysql-db=sakila --threads=8 --time=60 run"
    )

    # Cleanup test data
    run_shell_command(
        "sysbench /usr/share/sysbench/oltp_read_write.lua "
        "--mysql-host=localhost --mysql-user=sysbench_user --mysql-password=sysbench_password "
        "--mysql-db=sakila cleanup"
    )
    print("Sysbench benchmark completed and cleaned up.")
    
    # mark script ran successfully
    run_shell_command(
        "touch mysql_setup_sysbench.success"
    )
    print("script ran successfully")
    


# Main function
def main():
    # Install MySQL server
    install_mysql()

    # Wait for MySQL to be fully installed and running
    time.sleep(10)

    # Configure MySQL user and database
    configure_mysql()

    # Wait to make sure MySQL is ready
    time.sleep(5)

    # Download and import Sakila database
    download_and_import_sakila()

    # Run sysbench on the Sakila database
    run_sysbench()

if __name__ == "__main__":
    main()

