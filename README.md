# VLS Lambda

## Description
AWS Lambda function to retrieve bike sharing stations data from JCDecaux API and store it in an S3 bucket. This project provides a serverless solution for collecting and storing real-time data from JCDecaux bike sharing systems.

## Features
- Retrieves real-time data from JCDecaux bike sharing stations
- Stores data in JSON format in an S3 bucket with timestamped filenames
- Structured JSON logging for better monitoring and troubleshooting
- Comprehensive error handling and reporting
- Automated deployment using AWS SAM/CloudFormation
- Unit tests for reliable code quality

## Architecture
```
+-------------+     +-------------+     +-------------+
| CloudWatch  |---->|  Lambda     |---->|  JCDecaux   |
| Events      |     |  Function   |     |  API        |
+-------------+     +------+------+     +-------------+
                           |
                           v
                    +-------------+     +-------------+
                    |  S3 Bucket  |---->|  Data       |
                    |  Storage    |     |  Analytics  |
                    +-------------+     +-------------+
```

## Requirements
- Python 3.9 or higher
- AWS CLI configured with appropriate permissions
- JCDecaux API key (register at https://developer.jcdecaux.com/)

## Project Structure
- `lambda_modernized.py` - Main Lambda function code
- `logger_config.py` - Structured logging configuration
- `template.yaml` - AWS SAM/CloudFormation template
- `requirements.txt` - Python dependencies
- `test_lambda.py` - Unit tests
- `deploy.sh` - Deployment script

## Setup and Deployment

### Local Development
1. Clone the repository
   ```bash
   git clone https://github.com/sonytricoire/vls-lambda.git
   cd vls-lambda
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run tests
   ```bash
   python -m unittest test_lambda.py
   ```

### AWS Deployment
1. Make the deployment script executable
   ```bash
   chmod +x deploy.sh
   ```

2. Deploy to AWS
   ```bash
   ./deploy.sh --env dev --s3-bucket your-deployment-bucket --contract paris --api-key your-api-key
   ```

## Environment Variables
- `CONTRACT`: JCDecaux contract name (city)
- `API_KEY`: JCDecaux API key
- `BUCKET_NAME`: S3 bucket for storage
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENVIRONMENT`: Deployment environment (dev, test, prod)

## Security Best Practices
- Use AWS IAM roles instead of access keys
- Store sensitive information in AWS Secrets Manager
- Implement least privilege permissions
- Enable encryption for S3 bucket data

## Monitoring and Maintenance
- CloudWatch Logs for Lambda function execution
- CloudWatch Metrics for performance monitoring
- S3 lifecycle policies for data retention

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.