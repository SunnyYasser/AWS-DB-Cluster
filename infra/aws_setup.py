import json
import boto3
import constants

def create_vpc_and_subnet(ec2_client, ec2_resource):
    try:
        # Create VPC
        vpc_response = ec2_client.create_vpc(CidrBlock=constants.VPC_CIDR_BLOCK)
        vpc_id = vpc_response['Vpc']['VpcId']
        ec2_client.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": "MySQL-VPC"}])

        # Enable DNS support and DNS hostname
        ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
        ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})

        vpc = ec2_resource.Vpc(vpc_id)
        vpc.wait_until_available()

        # Create Subnet
        subnet = ec2_resource.create_subnet(VpcId=vpc.id, CidrBlock=constants.PUBLIC_CIDR_BLOCK)

        # Create and attach IGW to VPC
        ig = ec2_resource.create_internet_gateway()
        vpc.attach_internet_gateway(InternetGatewayId=ig.id)

        # Create Route Table and associate it
        route_table = vpc.create_route_table()
        route_table.create_route(DestinationCidrBlock=constants.IG_DEST_CIDR_BLOCK, GatewayId=ig.id)
        route_table.associate_with_subnet(SubnetId=subnet.id)

        print("Created VPC and Subnet successfully.")
        return vpc, vpc_id, subnet

    except Exception as e:
        print(f"Error creating VPC and Subnet: {e}")
        return None, None, None

def create_security_groups(ec2_client, vpc_id, ssh_allowed_ip):
    try:
        security_groups = {}

        # Create security groups
        groups_to_create = [
            ('gatekeeper', 'Internet-facing security group'),
            ('trusted_host', 'Trusted host security group'),
            ('proxy_manager', 'Proxy manager security group'),
            ('mysql_nodes', 'MySQL nodes security group')
        ]

        for name, description in groups_to_create:
            sg = ec2_client.create_security_group(
                GroupName=f'{name.upper()}_SG',
                Description=description,
                VpcId=vpc_id
            )
            security_groups[name] = sg['GroupId']
            print(f"Created {name} security group: {sg['GroupId']}")

        # Define Ingress and Egress rules for all security groups
        sg_rules = {
            'gatekeeper': [
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': ssh_allowed_ip}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ],
            'trusted_host': [
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': ssh_allowed_ip}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ],
            'proxy_manager': [
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': ssh_allowed_ip}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ],
            'mysql_nodes': [
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': ssh_allowed_ip}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        }

        # Authorize Ingress and Egress rules
        for sg_name, rules in sg_rules.items():
            sg_id = security_groups[sg_name]
            for rule in rules:
                ec2_client.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[rule])
                print(f"Configured ingress rule for {sg_name}")

        print("Security groups and rules configured successfully.")
        return security_groups ['gatekeeper'], security_groups ['trusted_host'], security_groups ['proxy_manager'], security_groups ['mysql_nodes'] 

    except Exception as e:
        print(f"Error creating security groups: {e}")
        return None

