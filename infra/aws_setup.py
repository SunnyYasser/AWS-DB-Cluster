import boto3
import json
import constants

def create_vpc_and_subnet(ec2_client, ec2):
    vpc_response = ec2_client.create_vpc(CidrBlock=constants.VPC_CIDR_BLOCK  )
    vpc_id = vpc_response['Vpc']['VpcId']
    ec2_client.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": "MySQL-VPC"}])

    # Enable DNS support and DNS hostname
    ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
    ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
    
    vpc = ec2.Vpc(vpc_id)
    vpc.wait_until_available()
    
    subnet = ec2.create_subnet(VpcId=vpc.id, CidrBlock=constants.PUBLIC_CIDR_BLOCK  )
    
    ig = ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=ig.id)
    
    route_table = vpc.create_route_table()
    route_table.create_route(DestinationCidrBlock=constants.IG_DEST_CIDR_BLOCK, GatewayId=ig.id)
    route_table.associate_with_subnet(SubnetId=subnet.id)
    
    print("Created vpc and subnet...")
    return vpc, vpc_id, subnet


def create_security_groups(ec2_client, vpc_id, ssh_allowed_ip):
    try:
        # Create security group 
        mysql_sg = ec2_client.create_security_group(
            GroupName='MYSQL_SG',
            Description='Security Group',
            VpcId=vpc_id
        )
        mysql_sg_id = mysql_sg['GroupId']
        
        print(f"Created Security Group: {mysql_sg_id}")
                
        ec2_client.authorize_security_group_ingress(
            GroupId=mysql_sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow HTTP from all IPs
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': ssh_allowed_ip}]  # Allow SSH from specific IPs
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow HTTPS from all IPs
                },
                {
                    'IpProtocol': 'icmp',  # ICMP protocol
                    'FromPort': -1,        # -1 indicates all ICMP types
                    'ToPort': -1,          # -1 indicates all ICMP codes
                    'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow ICMP from all IPs (for ping)
                }
            ]
        )
        
        print(f"Ingress rules set for Security Group: {mysql_sg_id}")
        return mysql_sg_id
    
    except Exception as e:
        print(f"Error creating security groups: {e}")
        return None, None
