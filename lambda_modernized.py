# -*- coding: utf-8 -*-
"""
Lambda function to retrieve data from JCDecaux bike sharing stations (VLS)
and store it in an S3 bucket.

Modernized version for Python 3.9+ and current AWS Lambda best practices.
"""

# Import required libraries
import os
import json
import logging
import http.client
import boto3
import time
import io
import requests
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, Union

# Import custom logger configuration
from logger_config import setup_logging

# Configure structured logging
logger = setup_logging()

# Get environment variables with fallbacks
def get_env_var(var_name: str, default: Optional[str] = None) -> str:
    """
    Safely retrieve environment variables with optional default values.
    
    Args:
        var_name: Name of the environment variable
        default: Optional default value if variable is not set
        
    Returns:
        The value of the environment variable or default
        
    Raises:
        ValueError: If the variable is not set and no default is provided
    """
    value = os.environ.get(var_name, default)
    if value is None:
        logger.error(f"Required environment variable {var_name} is not set")
        raise ValueError(f"Required environment variable {var_name} is not set")
    return value

# Retrieve environment variables
try:
    contract = get_env_var('CONTRACT')
    api_key = get_env_var('API_KEY')
    bucket_name = get_env_var('BUCKET_NAME')
    
    # Note: In a production environment, use IAM roles instead of access keys
    # These are included for backward compatibility
    key_id = get_env_var('KEY_ID', None)
    key_secret = get_env_var('KEY_SECRET', None)
except ValueError as e:
    logger.error(f"Configuration error: {str(e)}")
    # We'll handle this in the handler

# Initialize S3 client
def get_s3_client():
    """
    Get an S3 client using either IAM role or access keys if provided.
    
    Returns:
        boto3.client: Configured S3 client
    """
    if key_id and key_secret:
        # Using access keys (not recommended for production)
        logger.warning("Using AWS access keys instead of IAM roles")
        return boto3.client('s3',
                          aws_access_key_id=key_id,
                          aws_secret_access_key=key_secret)
    else:
        # Using IAM role (recommended)
        return boto3.client('s3')

# HTTP request headers
headers = {'Content-type': 'application/json'}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda function handler that is triggered by AWS Lambda.
    
    Args:
        event: Event data from AWS Lambda trigger
        context: Runtime information provided by AWS Lambda
        
    Returns:
        dict: Response with status and message
    """
    # Add AWS request ID to logger context if available
    if context and hasattr(context, 'aws_request_id'):
        logger.info("Lambda execution started", extra={
            'aws_request_id': context.aws_request_id,
            'event_source': event.get('source', 'unknown')
        })
    
    # Check if all required environment variables are set
    try:
        # Validate environment variables
        contract = get_env_var('CONTRACT')
        api_key = get_env_var('API_KEY')
        bucket_name = get_env_var('BUCKET_NAME')
    except ValueError as e:
        logger.error(f"Missing environment variable", extra={'error': str(e)})
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }
    
    try:
        # Build the API URL
        api_url = f'https://api.jcdecaux.com/vls/v1/stations'
        
        # Set up parameters
        params = {
            'contract': contract,
            'apiKey': api_key
        }
        
        # Log API request (without sensitive data)
        logger.info(f"Requesting data from JCDecaux API", extra={
            'contract': contract,
            'endpoint': api_url
        })
        
        # Make HTTP request to JCDecaux API using requests library with timeout
        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=5  # 5 seconds timeout
        )
        
        # Log response status
        logger.info(f"API response received", extra={
            'status_code': response.status_code,
            'contract': contract,
            'response_time_ms': int(response.elapsed.total_seconds() * 1000)
        })
        
        # Check if the request was successful (HTTP 200)
        if response.status_code == 200:
            # Get the response content
            result = response.text
            
            # Parse JSON to validate and count stations
            stations_data = json.loads(result)
            station_count = len(stations_data)
            
            logger.info(f"Successfully retrieved station data", extra={
                'station_count': station_count,
                'contract': contract
            })
            
            # Upload the data to S3
            upload_success = upload_to_s3(result)
            
            if upload_success:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'success',
                        'message': f'Data for {contract} successfully retrieved and stored',
                        'metadata': {
                            'station_count': station_count,
                            'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        }
                    })
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'status': 'error',
                        'message': 'Failed to upload data to S3'
                    })
                }
        else:
            # Log error details
            logger.error(f"API request failed", extra={
                'status_code': response.status_code,
                'contract': contract,
                'error_message': response.text[:200]  # Truncate long error messages
            })
            
            return {
                'statusCode': response.status_code,
                'body': json.dumps({
                    'status': 'error',
                    'message': f'API request failed with status code: {response.status_code}'
                })
            }
                
    except requests.exceptions.Timeout:
        logger.error("API request timed out", extra={'contract': contract})
        return {
            'statusCode': 504,
            'body': json.dumps({
                'status': 'error',
                'message': 'API request timed out'
            })
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error", extra={'error': str(e), 'contract': contract})
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': f'Request error: {str(e)}'
            })
        }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response", extra={'error': str(e), 'contract': contract})
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': f'Invalid JSON response: {str(e)}'
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error", extra={'error': str(e), 'contract': contract})
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            })
        }


def upload_to_s3(content: str) -> bool:
    """
    Upload content to an S3 bucket with a timestamped filename.
    
    Args:
        content: The content to upload to S3
        
    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        # Get S3 client
        s3 = get_s3_client()
        
        # Generate timestamp for the filename
        timestr = time.strftime("%Y%m%d-%H%M%S")
        
        # Create filename with contract name and timestamp
        filename = f"{contract}-{timestr}.json"
        
        # Create a file-like object from the content string
        fake_handle = io.StringIO(content)
        
        # Upload the content to S3 bucket with the generated filename
        s3.put_object(
            Bucket=bucket_name, 
            Key=filename, 
            Body=fake_handle.read(),
            ContentType='application/json'
        )

        # Log successful upload
        logger.info(f"File '{filename}' uploaded to S3 bucket '{bucket_name}'")
        return True
        
    except ClientError as e:
        logger.error(f"S3 upload error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during S3 upload: {str(e)}")
        return False