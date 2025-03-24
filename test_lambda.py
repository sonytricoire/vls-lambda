import unittest
import json
import os
from unittest.mock import patch, MagicMock
import lambda_modernized

class TestLambdaFunction(unittest.TestCase):
    """Test cases for the VLS Lambda function"""

    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        os.environ['CONTRACT'] = 'paris'
        os.environ['API_KEY'] = 'test-api-key'
        os.environ['BUCKET_NAME'] = 'test-bucket'
        
        # Sample API response
        self.sample_stations = '''[
            {
                "number": 123,
                "name": "Test Station",
                "address": "123 Test Street",
                "position": {
                    "lat": 48.8566,
                    "lng": 2.3522
                },
                "status": "OPEN",
                "bike_stands": 20,
                "available_bike_stands": 10,
                "available_bikes": 10,
                "last_update": 1617282000000
            }
        ]'''

    @patch('requests.get')
    def test_successful_api_call(self, mock_get):
        """Test successful API call and S3 upload"""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.sample_stations
        mock_response.elapsed.total_seconds.return_value = 0.1
        
        # Set up the mock
        mock_get.return_value = mock_response
        
        # Mock S3 client
        with patch('lambda_modernized.get_s3_client') as mock_s3:
            mock_s3_client = MagicMock()
            mock_s3.return_value = mock_s3_client
            
            # Call the lambda handler
            event = {}
            context = {}
            response = lambda_modernized.lambda_handler(event, context)
            
            # Verify the response
            self.assertEqual(response['statusCode'], 200)
            self.assertIn('success', json.loads(response['body'])['status'])
            
            # Verify S3 upload was called
            mock_s3_client.put_object.assert_called_once()

    @patch('requests.get')
    def test_api_error(self, mock_get):
        """Test handling of API error"""
        # Mock HTTP response with error
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = '{ "error" : "Unauthorized" }'
        mock_response.elapsed.total_seconds.return_value = 0.1
        
        # Set up the mock
        mock_get.return_value = mock_response
        
        # Call the lambda handler
        event = {}
        context = {}
        response = lambda_modernized.lambda_handler(event, context)
        
        # Verify the response
        self.assertEqual(response['statusCode'], 403)
        self.assertIn('error', json.loads(response['body'])['status'])

    def test_missing_environment_variable(self):
        """Test handling of missing environment variable"""
        # Remove required environment variable
        del os.environ['CONTRACT']
        
        # Call the lambda handler
        event = {}
        context = {}
        response = lambda_modernized.lambda_handler(event, context)
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        self.assertIn('error', json.loads(response['body'])['status'])
        self.assertIn('CONTRACT', json.loads(response['body'])['message'])
        
        # Restore environment variable for other tests
        os.environ['CONTRACT'] = 'paris'

if __name__ == '__main__':
    unittest.main()