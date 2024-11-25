from aws_setup import create_vpc_and_subnet, create_security_groups
from ec2_manager import create_instances, wait_for_instances
from app_deployment import deploy_master_app, deploy_slave_apps, deploy_proxy_manager_app, deploy_gatekeeper_app, deploy_trusted_host_app
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
    gatekeeper_sg, trusted_host_sg, proxy_manager_sg, mysql_sg = create_security_groups (ec2_client, vpc_id, my_ip_cidr)
    
    # Launch EC2 instances
    mysql_instances = create_instances(ec2, constants.MYSQL_NODE_TYPE, constants.MYSQL_NODE_COUNT, subnet, mysql_sg, 'MySQLNodes', keypair)
    proxy_mgr_instance = create_instances(ec2, constants.PROXY_MANAGER_NODE_TYPE, constants.PROXY_MANAGER_NODE_COUNT, subnet, proxy_manager_sg, 'ProxyManagerNode', keypair)
    trusted_host_instance = create_instances(ec2, constants.TRUSTED_HOST_NODE_TYPE, constants.TRUSTED_HOST_NODE_COUNT, subnet, trusted_host_sg, 'TrustedHostNode', keypair)
    gatekeeper_instance = create_instances(ec2, constants.GATEKEEPER_NODE_TYPE, constants.GATEKEEPER_NODE_COUNT, subnet, gatekeeper_sg, 'GateKeeperNode', keypair)
    
    time.sleep(60)

    instance_data = []
    proxy_mgr_data = []
    gatekeeper_data = []
    trusted_host_data = []
 
    for i, instance in enumerate(mysql_instances, start=1):
        instance.wait_until_running()
        instance.load()
        
        if i == 1:
            instance_name = f'mysql_master_node'
        else:
            instance_name = f'mysql_slave_node'

        instance.create_tags(Tags=[{'Key': 'Name', 'Value': instance_name}])
 
        instance_info = {
            'Name': instance_name,
            'InstanceID': instance.id,
            'PublicDNS': instance.public_dns_name,
            'PublicIP': instance.public_ip_address
        }

        instance_data.append(instance_info)
    
    for i, instance in enumerate(proxy_mgr_instance, start=1):
        instance.wait_until_running()
        instance.load()
        
        instance_name = f'proxy_manager_node'

        instance.create_tags(Tags=[{'Key': 'Name', 'Value': instance_name}])
 
        instance_info = {
            'Name': instance_name,
            'InstanceID': instance.id,
            'PublicDNS': instance.public_dns_name,
            'PublicIP': instance.public_ip_address
        }

        proxy_mgr_data.append(instance_info)
    
    for i, instance in enumerate(gatekeeper_instance, start=1):
        instance.wait_until_running()
        instance.load()
        
        instance_name = f'gatekeeper_node'

        instance.create_tags(Tags=[{'Key': 'Name', 'Value': instance_name}])
 
        instance_info = {
            'Name': instance_name,
            'InstanceID': instance.id,
            'PublicDNS': instance.public_dns_name,
            'PublicIP': instance.public_ip_address
        }

        gatekeeper_data.append(instance_info)
    
    for i, instance in enumerate(trusted_host_instance, start=1):
        instance.wait_until_running()
        instance.load()
        
        instance_name = f'trusted_host_node'

        instance.create_tags(Tags=[{'Key': 'Name', 'Value': instance_name}])
 
        instance_info = {
            'Name': instance_name,
            'InstanceID': instance.id,
            'PublicDNS': instance.public_dns_name,
            'PublicIP': instance.public_ip_address
        }

        trusted_host_data.append(instance_info)
    
    save_json (instance_data, "../mysql/master/instance_details.json")
    save_json (instance_data, "../mysql/proxy_manager/instance_details.json")
    save_json (proxy_mgr_data, "../mysql/trusted_host/proxy_manager_details.json")
    save_json (trusted_host_data, "../mysql/gatekeeper/trusted_host_details.json")
    save_json (gatekeeper_data, "../client/gatekeeper_details.json")
    print("Instance details saved to json files")
    
    deploy_master_app ()
    deploy_slave_apps ()
    deploy_proxy_manager_app ()
    deploy_gatekeeper_app ()
    deploy_trusted_host_app ()

if __name__ == "__main__":
    main()

