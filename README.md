# vls-lambda

## Description
AWS Lambda function to retrieve bike sharing stations data from JCDecaux API and store it in an S3 bucket.

## Features
- Retrieves real-time data from JCDecaux bike sharing stations
- Stores data in JSON format in an S3 bucket
- Uses timestamped filenames for easy data tracking

## Requirements
- AWS Lambda environment
- Environment variables:
  - CONTRACT: JCDecaux contract name (city)
  - API_KEY: JCDecaux API key
  - BUCKET_NAME: S3 bucket for storage
  - KEY_ID: AWS access key ID
  - KEY_SECRET: AWS secret access key

## Usage
This function is designed to be triggered by AWS Lambda events (e.g., CloudWatch scheduled events).
