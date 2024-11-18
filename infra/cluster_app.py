from fastapi import FastAPI, Request
import boto3
import socket
import psutil
import time
from ec2_metadata import ec2_metadata
import logging
from datetime import datetime, timezone, timedelta

access_key_id = {my_aws_access_key_id}
secret_access_key = {my_aws_secret_access_key}
session_token = {my_aws_session_token}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('uvicorn-error')

app = FastAPI()
cloudwatch = boto3.client('cloudwatch', aws_access_key_id=access_key_id,
                        aws_secret_access_key=secret_access_key,
                        aws_session_token=session_token,
                        region_name='us-east-1')

ec2 = boto3.resource('ec2', aws_access_key_id=access_key_id,
                        aws_secret_access_key=secret_access_key,
                        aws_session_token=session_token,
                        region_name='us-east-1')

def put_metric_data(metric_name, value, unit='Count'):
    instance_id = ec2_metadata.instance_id
    cloudwatch.put_metric_data(
        Namespace='CustomMetrics',
        MetricData=[
            {
                'MetricName': metric_name,
                'Dimensions': [
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    },
                ],
                'Unit': unit,
                'Value': value
            },
        ]
    )

def increment_request_count ():
    instance_id = ec2_metadata.instance_id

    # Fetch the current request count and increment it
    response = cloudwatch.get_metric_statistics(
        Namespace='CustomMetrics',
        MetricName='RequestCount',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=datetime.now (timezone.utc) - timedelta(minutes=1),
        EndTime=datetime.now (timezone.utc),
        Period=60,
        Statistics=['Sum']
    )

    # Default request count is 1 if there is no metric data
    request_count = 1
    if len(response['Datapoints']) > 0:
        request_count += response['Datapoints'][0]['Sum']

    # Push the updated request count to CloudWatch
    put_metric_data('RequestCount', request_count, 'Count')


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    put_metric_data('ResponseTime', process_time, 'Seconds')
    return response

@app.get("/")
def read_root():
    increment_request_count ()
    
    # CPU Usage
    cpu_percent = psutil.cpu_percent()
    put_metric_data('CPUUtilization', cpu_percent, 'Percent')
    logger.info(f"CPUUtilization =  {cpu_percent}" )
    
    # Memory Usage
    memory = psutil.virtual_memory()
    put_metric_data('MemoryUtilization', memory.percent, 'Percent')
    logger.info(f"VMem =  {memory.percent}" )
    
    # Disk Usage
    disk = psutil.disk_usage('/')
    put_metric_data('DiskUtilization', disk.percent, 'Percent')
    logger.info(f"DiskUtil =  {disk.percent}" )
    
    instance_id = ec2_metadata.instance_id
    return  f"Hello from cluster 1, instance {instance_id}"
