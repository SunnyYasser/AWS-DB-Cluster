import paramiko
import os
import json
import time
from capture_aws_credentials2 import get_aws_credentials
from constants import *

def upload_directory(ssh_client, local_directory):
    """
    Uploads an entire directory to the remote server via SFTP.

    :param ssh_client: The SSH client object.
    :param local_directory: The local directory to upload.
    """
    if local_directory == "master":
        local_directory = "../mysql/master"

    elif local_directory == "slave":
        local_directory = "../mysql/slave"
    
    elif local_directory == "proxy_manager":
        local_directory = "../mysql/proxy_manager"

    elif local_directory == "trusted_host":
        local_directory = "../mysql/trusted_host"

    else:
        local_directory = "../mysql/gatekeeper"

    local_absolute_path = os.path.abspath(local_directory)
    
    # Start SFTP session
    sftp = ssh_client.open_sftp()
    
    print(f"Uploading files in {local_absolute_path}")

    try:
        for item in os.listdir(local_directory):
            local_path = os.path.join(local_absolute_path, item)
            remote_app_path = f"/home/ubuntu/{item}"                
            print('remote_app_path',remote_app_path)
            print(f"Uploading {local_path} to {remote_app_path}")
            
            sftp.put(local_path, remote_app_path)
            
            print(f"Uploaded {local_path} to {remote_app_path}")

    finally:
        sftp.close()  # Close the SFTP session


def setup_non_db_deployment (path, app_name, public_ip, instance_id):
    install_commands = [
        'sudo apt-get update',
        'sudo apt install python3 python3-pip -y',
        'sudo pip3 install flask gunicorn requests boto3'
    ]

    try:
        print(f"Connecting to {public_ip} for {instance_id} in {path}...")

        # Initialize SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(public_ip, username='ubuntu', key_filename=SECRET_KEY_PATH)

        print(f"Connected to {public_ip} for {instance_id} in {path}...")
        
        for install_command in install_commands:
            stdin, stdout, stderr = ssh.exec_command(install_command)
            stdout.channel.recv_exit_status()  # Wait for the command to finish
        
            print(f"Completed running {install_command} ...")    
            
            output = stdout.read().decode()
            error_output = stderr.read().decode()

        print(f"Completed running start commands for {public_ip} in {path}...")
        
        upload_directory (ssh, path)
        print(f"Completed uploading files for {public_ip} in {path}...")
        
        stdin, stdout, stderr = ssh.exec_command (f"sudo gunicorn {app_name.split('/')[-1].split('.')[0]}:app -w 4 --bind 0.0.0.0:80 --log-level info &")
        stdout.channel.recv_exit_status()
        print(f"Completed deploying {app_name} at {public_ip} in {path}...")
    
    except Exception as e:
        print(f"Error deploying to {public_ip}: {e}")
    finally:
        ssh.close()

def setup_deployment (path, app_name, public_ip, instance_id):
    install_commands = [
        'sudo apt-get update',
        'sudo apt install python3 python3-pip -y',
        'sudo pip3 install flask gunicorn requests boto3',
        'sudo pip3 install mysql-connector-python'
    ]

    try:
        print(f"Connecting to {public_ip} for {instance_id} in {path}...")

        # Initialize SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(public_ip, username='ubuntu', key_filename=SECRET_KEY_PATH)

        print(f"Connected to {public_ip} for {instance_id} in {path}...")
        
        for install_command in install_commands:
            stdin, stdout, stderr = ssh.exec_command(install_command)
            stdout.channel.recv_exit_status()  # Wait for the command to finish
        
            print(f"Completed running {install_command} ...")    
            
            output = stdout.read().decode()
            error_output = stderr.read().decode()

        print(f"Completed running start commands for {public_ip} in {path}...")
        
        upload_directory (ssh, path)
        print(f"Completed uploading files for {public_ip} in {path}...")
        
        stdin, stdout, stderr = ssh.exec_command (f"python3 mysql_setup_sysbench.py")
        stdout.channel.recv_exit_status()
        print(f"Completed installing mysql and running sysbench on sakila")
        print(stdout.read().decode())

        stdin, stdout, stderr = ssh.exec_command (f"sudo gunicorn {app_name.split('/')[-1].split('.')[0]}:app -w 4 --bind 0.0.0.0:80 --log-level info &")
        stdout.channel.recv_exit_status()
        print(f"Completed deploying {app_name} at {public_ip} in {path}...")
    
    except Exception as e:
        print(f"Error deploying to {public_ip}: {e}")
    finally:
        ssh.close()

def set_credentials (filename):

    credentials = get_aws_credentials ()

    with open (filename, 'r') as file:
        code = file.read()

    aws_access_key_id = f"'{str(credentials['aws_access_key_id'])}'"
    aws_secret_access_key = f"'{credentials['aws_secret_access_key']}'"
    aws_session_token = f"'{credentials['aws_session_token']}'"
    
    code1 = code.replace("{my_aws_access_key_id}", aws_access_key_id)
    code2 = code1.replace("{my_aws_secret_access_key}", aws_secret_access_key)
    code3 = code2.replace("{my_aws_session_token}", aws_session_token)

    with open(filename, 'w') as file:
        file.write(code3)

def deploy_master_app ():
    #Specify the instance IDs
    with open('../mysql/master/instance_details.json', 'r') as file:
         instance_details = json.load(file)
    
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        if instance['Name'] == 'mysql_master_node':
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])

    setup_deployment ("master", "master_app.py", public_ips[0], instance_ids[0])

def deploy_slave_apps ():
    #Specify the instance IDs
    with open('../mysql/master/instance_details.json', 'r') as file:
         instance_details = json.load(file)
 
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        if instance['Name'] != 'mysql_master_node':
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])

    for i, ip in enumerate (public_ips):
        setup_deployment ("slave", "slave_app.py", ip, instance_ids[i])

def deploy_proxy_manager_app ():
    #Specify the instance IDs
    with open('../mysql/trusted_host/proxy_manager_details.json', 'r') as file:
         instance_details = json.load(file)
    
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        instance_ids.append(instance['InstanceID'])
        public_ips.append(instance['PublicIP'])
    
    setup_non_db_deployment ("proxy_manager", "proxy_manager_app.py", public_ips[0], instance_ids[0])

def deploy_trusted_host_app ():
    #Specify the instance IDs
    with open('../mysql/gatekeeper/trusted_host_details.json', 'r') as file:
         instance_details = json.load(file)
    
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        instance_ids.append(instance['InstanceID'])
        public_ips.append(instance['PublicIP'])

    setup_non_db_deployment ("trusted_host", "trusted_host_app.py", public_ips[0], instance_ids[0])

def deploy_gatekeeper_app ():
    #Specify the instance IDs
    with open('../client/gatekeeper_details.json', 'r') as file:
         instance_details = json.load(file)
    
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        instance_ids.append(instance['InstanceID'])
        public_ips.append(instance['PublicIP'])

    setup_non_db_deployment ("gatekeeper", "gatekeeper_app.py", public_ips[0], instance_ids[0])
