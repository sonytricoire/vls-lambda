import os
import httplib
import logging
import boto3
import time
from cStringIO import StringIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

contract = os.environ['CONTRACT']
apiKey = os.environ['API_KEY']
bucketName = os.environ['BUCKET_NAME']
keyId = os.environ['KEY_ID']
keySecret = os.environ['KEY_SECRET']

s3 = boto3.client('s3',
        aws_access_key_id=keyId,
        aws_secret_access_key=keySecret)

headers = {'Content-type': 'application/json'}

connection = httplib.HTTPSConnection('api.jcdecaux.com')

def lambda_handler(event, context):
    
    connection.request('GET', '/vls/v1/stations?contract=' + contract + '&apiKey=' + apiKey, '', headers)
   
    response = connection.getresponse()
    logger.info('Downloaded ' + contract + ' stations : {} '.format(response.status))
    
    if response.status == 200:
        result = response.read().decode()
        uploadToS3(result)
        return 'ok'
            
    return 'ko'


def uploadToS3(content):
    
    timestr = time.strftime("%Y%m%d-%H%M%S")
    filename = contract + '-' + timestr + '.json'
    
    fake_handle = StringIO(content)
    # notice if you do fake_handle.read() it reads like a file handle
    s3.put_object(Bucket=bucketName, Key=filename, Body=fake_handle.read())

    logger.info(filename + 'uploaded to s3')
    