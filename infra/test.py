import paramiko
import os
import json
import time

def upload_directory(ssh_client, local_directory):
    """
    Uploads an entire directory to the remote server via SFTP.

    :param ssh_client: The SSH client object.
    :param local_directory: The local directory to upload.
    :param remote_directory: The remote directory to upload to.
    """
    if local_directory == "orchestrator":
        local_directory = "../orchestrator"

    if local_directory == "worker":
        local_directory = "../worker"

    local_absolute_path = os.path.abspath(local_directory)

    # Start SFTP session
    sftp = ssh_client.open_sftp()
    
    print(f"Uploading files in {local_absolute_path}")

    try:
        for item in os.listdir(local_directory):
            local_path = os.path.join(local_absolute_path, item)
            remote_app_path = f"/home/ubuntu/{local_path.split('/')[-1]}"

            print(f"Uploading {local_path} to {remote_app_path}")
            
            sftp.put(local_path, remote_app_path)
            
            print(f"Uploaded {local_path} to {remote_app_path}")

    finally:
        sftp.close()  # Close the SFTP session


def setup_deployment (path, public_ip, instance_id):
    install_commands = [
        # Install docker
        'sudo apt-get update',
        'sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common',
        'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -',
        'sudo add-apt-repository "deb https://download.docker.com/linux/ubuntu jammy stable" -y',
        'sudo apt-get update',
        'sudo apt-cache policy docker-ce',
        'sudo apt-get install -y docker-ce',
        'sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose',
        'sudo chmod +x /usr/local/bin/docker-compose'
    ]

    try:
        print(f"Connecting to {public_ip} for {instance_id} in {path}...")

        # Initialize SSH client
        private_key_path = 'EHPS_LOG8415E_Assignment2_keypair.pem'
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(public_ip, username='ubuntu', key_filename=private_key_path)

        print(f"Connected to {public_ip} for {instance_id} in {path}...")
        
        for install_command in install_commands:
            stdin, stdout, stderr = ssh.exec_command(install_command)
            stdout.channel.recv_exit_status()  # Wait for the command to finish
        
            print(f"Completed running {install_command} ...")


        print(f"Completed running start commands for {public_ip} in {path}...")
        
        upload_directory (ssh, path)
        
        print(f"Completed uploading files for {public_ip} in {path}...")
        

        print(f"Starting docker containers for {public_ip} in {path}...")

        start_command = "sudo docker-compose up --build"
        stdin, stdout, stderr = ssh.exec_command(start_command)
        stdout.channel.recv_exit_status()  # Wait for the command to finish

        print(f"Docker app deployed and running on {public_ip} for {path}")
    

    except Exception as e:
        print(f"Error deploying to {public_ip}: {e}")
    finally:
        ssh.close()


def deploy_orchestrator_app ():
    #Specify the instance IDs
    with open('instance_details.json', 'r') as file:
         instance_details = json.load(file)
 
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        if instance['Name'] == 'orchestrator':
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])


    print(instance_ids)
    print(public_ips)
    setup_deployment ("orchestrator", public_ips[0], instance_ids[0])

if __name__ == "__main__":
    deploy_orchestrator_app()
