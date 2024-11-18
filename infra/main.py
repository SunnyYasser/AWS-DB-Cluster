from aws_setup import create_vpc_and_subnet, create_security_groups
from ec2_manager import create_instances, wait_for_instances
from app_deployment import deploy_orchestrator_app, deploy_worker_apps
from create_keypair import create_keypair
from capture_aws_credentials2 import get_aws_credentials
import requests
import boto3
import ipaddress
import json
import constants
import time

def get_local_ip_cidr ():
    response = requests.get('https://api.ipify.org')
    public_ip = response.text.strip()
    subnet_mask = '255.255.255.0'
    cidr_network = ipaddress.ip_network(f"{public_ip}/{subnet_mask}", strict=False)

    return str(cidr_network)

def load_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def save_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def get_public_ip (ec2_client, instance_id):
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress')

        if public_ip:
            return public_ip
        
        else:
            print(f"Instance {instance_id} does not have a public IP address.")
            return None
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



def main():
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    ec2_client = boto3.client('ec2', region_name='us-east-1')

    #create keypair
    keypair = create_keypair (ec2_client, "Sunny_LOG8415E_Assignment3_keypair")
    
    #get local machine IP for SSH
    my_ip_cidr = get_local_ip_cidr()

    # Set up VPC, subnet, and security groups
    vpc, vpc_id, subnet = create_vpc_and_subnet(ec2_client, ec2)
    mysql_sg = create_security_groups(ec2_client, vpc_id, my_ip_cidr)
    
    # Launch EC2 instances
    mysql_instances = create_instances(ec2, constants.MYSQL_NODE_TYPE, constants.MYSQL_NODE_COUNT, subnet, mysql_sg, 'MySQLNodes', keypair)
    #orchestrator_instance_list = create_instances(ec2, constants.CLUSTER2_TYPE, constants.CLUSTER2_COUNT, subnet, lb_sg, 'Orchestrator', keypair)
    #orchestrator_instance = orchestrator_instance_list[0]
    
    time.sleep(60)

    instance_data = []
 
    for i, instance in enumerate(mysql_instances, start=1):
        instance.wait_until_running()
        instance.load()
        
        if i < 3:
            instance_name = f'mysql_read_node_{i}'
        else:
            instance_name = f'mysql_write_node'

        instance.create_tags(Tags=[{'Key': 'Name', 'Value': instance_name}])
 
        instance_info = {
            'Name': instance_name,
            'InstanceID': instance.id,
            'PublicDNS': instance.public_dns_name,
            'PublicIP': instance.public_ip_address
        }

        instance_data.append(instance_info)
    
    
    save_json (instance_data, "instance_details.json")
    print("Instance details saved to instance_details.json")
    

if __name__ == "__main__":
    main()

