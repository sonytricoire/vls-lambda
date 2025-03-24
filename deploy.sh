#!/bin/bash
# Script to deploy the VLS Lambda function to AWS

set -e

# Default values
ENVIRONMENT="dev"
STACK_NAME="vls-data-collector"
S3_BUCKET=""
CONTRACT=""
API_KEY=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --stack-name)
      STACK_NAME="$2"
      shift 2
      ;;
    --s3-bucket)
      S3_BUCKET="$2"
      shift 2
      ;;
    --contract)
      CONTRACT="$2"
      shift 2
      ;;
    --api-key)
      API_KEY="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --env ENV             Deployment environment (dev, test, prod) [default: dev]"
      echo "  --stack-name NAME     CloudFormation stack name [default: vls-data-collector]"
      echo "  --s3-bucket BUCKET    S3 bucket for deployment artifacts"
      echo "  --contract CONTRACT   JCDecaux contract name (city)"
      echo "  --api-key KEY         JCDecaux API key"
      echo "  --help                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [ -z "$S3_BUCKET" ]; then
  echo "Error: S3 bucket is required (--s3-bucket)"
  exit 1
fi

if [ -z "$CONTRACT" ]; then
  echo "Error: JCDecaux contract is required (--contract)"
  exit 1
fi

if [ -z "$API_KEY" ]; then
  echo "Error: JCDecaux API key is required (--api-key)"
  exit 1
fi

# Set stack name with environment
STACK_NAME="${STACK_NAME}-${ENVIRONMENT}"

# Create a unique S3 bucket name for data storage if not provided
DATA_BUCKET_NAME="vls-data-${ENVIRONMENT}-$(date +%s)"

echo "=== Building deployment package ==="
# Create a temporary directory for the deployment package
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Install dependencies to the temporary directory
echo "Installing dependencies..."
pip install -r requirements.txt -t $TEMP_DIR

# Copy Lambda function code to the temporary directory
echo "Copying Lambda function code..."
cp lambda_modernized.py $TEMP_DIR/
cp logger_config.py $TEMP_DIR/

# Create deployment package
echo "Creating deployment package..."
cd $TEMP_DIR
zip -r ../deployment-package.zip .
cd -

echo "=== Deploying to AWS ==="
# Upload deployment package to S3
echo "Uploading deployment package to S3..."
aws s3 cp deployment-package.zip s3://$S3_BUCKET/

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack: $STACK_NAME..."
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=$ENVIRONMENT \
    JCDecauxContract=$CONTRACT \
    JCDecauxApiKey=$API_KEY \
    DataBucketName=$DATA_BUCKET_NAME \
  --s3-bucket $S3_BUCKET

# Clean up
echo "Cleaning up temporary files..."
rm -rf $TEMP_DIR
rm deployment-package.zip

echo "=== Deployment completed successfully ==="
echo "Stack name: $STACK_NAME"
echo "Data bucket: $DATA_BUCKET_NAME"

# Get Lambda function URL
FUNCTION_ARN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='VLSDataCollectorFunction'].OutputValue" --output text)
echo "Lambda function ARN: $FUNCTION_ARN"

echo "=== Next steps ==="
echo "1. Monitor the Lambda function in the AWS Console"
echo "2. Check CloudWatch Logs for execution details"
echo "3. Verify data is being stored in the S3 bucket: $DATA_BUCKET_NAME"