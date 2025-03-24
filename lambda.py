# -*- coding: utf-8 -*-
"""
Lambda function to retrieve data from JCDecaux bike sharing stations (VLS)
and store it in an S3 bucket.
"""

# Import required libraries
import os           # For accessing environment variables
import httplib      # For HTTP requests
import logging      # For event logging
import boto3        # AWS SDK for Python
import time         # For time-related operations
from cStringIO import StringIO  # To handle strings as files

# Logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set logging level to INFO

# Retrieve environment variables
contract = os.environ['CONTRACT']      # JCDecaux contract name (city)
apiKey = os.environ['API_KEY']         # API key for JCDecaux
bucketName = os.environ['BUCKET_NAME'] # S3 bucket name for storage
keyId = os.environ['KEY_ID']           # AWS key ID
keySecret = os.environ['KEY_SECRET']   # AWS secret key

# Initialize S3 client with AWS credentials
s3 = boto3.client('s3',
        aws_access_key_id=keyId,
        aws_secret_access_key=keySecret)

# HTTP request headers
headers = {'Content-type': 'application/json'}

# Establish HTTPS connection with JCDecaux API
connection = httplib.HTTPSConnection('api.jcdecaux.com')

def lambda_handler(event, context):
    """
    Main Lambda function handler that is triggered by AWS Lambda.
    
    Args:
        event (dict): Event data from AWS Lambda trigger
        context (object): Runtime information provided by AWS Lambda
        
    Returns:
        str: 'ok' if successful, 'ko' if failed
    """
    
    # Make HTTP request to JCDecaux API to get stations data for the specified contract
    connection.request('GET', '/vls/v1/stations?contract=' + contract + '&apiKey=' + apiKey, '', headers)
   
    # Get the response from the API
    response = connection.getresponse()
    logger.info('Downloaded ' + contract + ' stations : {} '.format(response.status))
    
    # Check if the request was successful (HTTP 200)
    if response.status == 200:
        # Read and decode the response content
        result = response.read().decode()
        # Upload the data to S3
        uploadToS3(result)
        return 'ok'
            
    # Return failure status if the request was not successful
    return 'ko'


def uploadToS3(content):
    """
    Upload content to an S3 bucket with a timestamped filename.
    
    Args:
        content (str): The content to upload to S3
    """
    
    # Generate timestamp for the filename
    timestr = time.strftime("%Y%m%d-%H%M%S")
    # Create filename with contract name and timestamp
    filename = contract + '-' + timestr + '.json'
    
    # Create a file-like object from the content string
    fake_handle = StringIO(content)
    # Upload the content to S3 bucket with the generated filename
    s3.put_object(Bucket=bucketName, Key=filename, Body=fake_handle.read())

    # Log successful upload
    logger.info(filename + ' uploaded to s3')