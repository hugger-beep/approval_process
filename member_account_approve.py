import json
import os
import boto3
import hmac
import hashlib
import base64
import urllib.parse
import logging
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def verify_signature(token, signature, timestamp):
    try:
        logger.info("Starting signature verification")
        secret = get_signing_secret()
        message = f"{token}:{timestamp}"
        expected_signature = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        is_valid = hmac.compare_digest(signature, expected_signature)
        logger.info(f"Signature verification result: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Signature verification error: {str(e)}", exc_info=True)
        raise

def get_signing_secret():
    try:
        logger.info("Attempting to retrieve secret")
        secret_name = "approval-process/signing-secret"
        region_name = "us-east-1"  # Update with your region
        
        session = boto3.session.Session()
        config = Config(
            connect_timeout=2,
            read_timeout=2,
            retries={'max_attempts': 2}
        )
        
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name,
            config=config
        )
        
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
            logger.info("Successfully retrieved secret")
            return secret['secret']
        else:
            raise ValueError("Secret value not found in response")
            
    except ClientError as e:
        logger.error(f"Error retrieving secret: {str(e)}", exc_info=True)
        raise

def validate_request_parameters(params):
    try:
        logger.info("Validating request parameters")
        if not params:
            logger.error("No query parameters found")
            return False

        token = params.get('token')
        signature = params.get('signature')
        timestamp = params.get('timestamp')

        if not all([token, signature, timestamp]):
            logger.error("Missing required parameters")
            return False

        try:
            # Verify timestamp format and not too old
            timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
            now = datetime.utcnow()
            if timestamp_dt < now - timedelta(hours=24):
                logger.error("Timestamp too old")
                return False
        except ValueError as e:
            logger.error(f"Invalid timestamp format: {str(e)}")
            return False

        return True
    except Exception as e:
        logger.error(f"Parameter validation error: {str(e)}", exc_info=True)
        return False

def update_dynamodb_status(token):
    try:
        logger.info(f"Updating DynamoDB for token: {token}")
        config = Config(
            connect_timeout=2,
            read_timeout=2,
            retries={'max_attempts': 2}
        )
        
        dynamodb = boto3.resource('dynamodb', config=config)
        table = dynamodb.Table('approval-tokens')
        
        current_time = datetime.utcnow().isoformat()
        
        response = table.update_item(
            Key={'token': token},
            UpdateExpression='SET #status = :status, #updateTime = :updateTime',
            ExpressionAttributeNames={
                '#status': 'status',
                '#updateTime': 'lastUpdateTime'
            },
            ExpressionAttributeValues={
                ':status': 'APPROVED',
                ':updateTime': current_time
            },
            ReturnValues='ALL_NEW'
        )
        
        logger.info(f"DynamoDB update successful: {response}")
        return response
    except Exception as e:
        logger.error(f"DynamoDB update error: {str(e)}", exc_info=True)
        raise

def send_sns_notification(token, timestamp):
    try:
        logger.info("Preparing approval SNS notification")
        config = Config(
            connect_timeout=2,
            read_timeout=2,
            retries={'max_attempts': 2}
        )
        
        sns = boto3.client('sns', config=config)
        message = f"""
        PATCHING REQUEST APPROVED
        ========================

        Customer has approved the patching request.

        APPROVAL DETAILS
        ----------------
        Customer approved patching at this time.

        ADDITIONAL INFORMATION
        --------------------
        Request ID: {token}
        Approval Date: {timestamp}

        This is an automated message. Please do not reply to this email.
        """

        response = sns.publish(
            TopicArn=os.environ['APPROVAL_TOPIC_ARN'],
            Message=message,
            Subject='Patching Request Approved'
        )
        logger.info(f"SNS notification sent successfully: {response}")
    except Exception as e:
        logger.error(f"SNS notification error: {str(e)}", exc_info=True)
        raise

def generate_html_response(success=True, error_message=None):
    if success:
        return """
        <html>
            <head>
                <title>Approval Processed</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 40px; 
                        line-height: 1.6;
                        color: #333;
                        background-color: #f9f9f9;
                    }
                    .container {
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #ffffff;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .approval { 
                        color: #2e7d32;
                        margin-bottom: 20px;
                        text-align: center;
                    }
                    .message {
                        background-color: #e8f5e9;
                        padding: 20px;
                        border-radius: 4px;
                        margin-bottom: 20px;
                        border-left: 4px solid #2e7d32;
                    }
                    .checkmark {
                        color: #2e7d32;
                        font-size: 48px;
                        text-align: center;
                        margin-bottom: 20px;
                    }
                    .footer {
                        text-align: center;
                        color: #666;
                        font-size: 0.9em;
                        margin-top: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="checkmark">✓</div>
                    <h1 class="approval">Approval Processed</h1>
                    <div class="message">
                        <p>The patching request has been approved successfully.</p>
                        <p>The security team has been notified and will proceed with the patching process.</p>
                        <p>You can now close this window.</p>
                    </div>
                    <div class="footer">
                        This is an automated response. Please do not reply to this message.
                    </div>
                </div>
            </body>
        </html>
        """
    else:
        return f"""
        <html>
            <head>
                <title>Error Processing Request</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 40px; 
                        line-height: 1.6;
                        color: #333;
                        background-color: #f9f9f9;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #ffffff;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .error {{ 
                        color: #d32f2f;
                        margin-bottom: 20px;
                        text-align: center;
                    }}
                    .message {{
                        background-color: #ffebee;
                        padding: 20px;
                        border-radius: 4px;
                        margin-bottom: 20px;
                        border-left: 4px solid #d32f2f;
                    }}
                    .footer {{
                        text-align: center;
                        color: #666;
                        font-size: 0.9em;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="error">Error Processing Request</h1>
                    <div class="message">
                        <p>An error occurred while processing your request.</p>
                        <p>{error_message if error_message else 'Please try again later or contact support.'}</p>
                    </div>
                    <div class="footer">
                        This is an automated response. Please contact support if the issue persists.
                    </div>
                </div>
            </body>
        </html>
        """

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Calculate remaining time
        remaining_time = context.get_remaining_time_in_millis() / 1000
        logger.info(f"Remaining time: {remaining_time} seconds")
        
        # Validate input parameters
        if not validate_request_parameters(event.get('queryStringParameters', {})):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'text/html'},
                'body': generate_html_response(False, "Missing or invalid parameters")
            }

        # Extract parameters
        params = event['queryStringParameters']
        token = params['token']
        signature = params['signature']
        timestamp = params['timestamp']

        # Verify signature
        if not verify_signature(token, signature, timestamp):
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'text/html'},
                'body': generate_html_response(False, "Invalid signature")
            }

        # Check remaining time before DynamoDB update
        if context.get_remaining_time_in_millis() < 2000:  # 2 seconds
            logger.error("Insufficient time remaining for DynamoDB update")
            raise TimeoutError("Function timeout imminent")

        # Update DynamoDB
        update_dynamodb_status(token)

        # Check remaining time before SNS
        if context.get_remaining_time_in_millis() < 2000:
            logger.error("Insufficient time remaining for SNS notification")
            raise TimeoutError("Function timeout imminent")

        # Send SNS notification
        send_sns_notification(token, timestamp)

        # Return success response
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': generate_html_response(True)
        }

    except TimeoutError as te:
        logger.error(f"Timeout error: {str(te)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': generate_html_response(False, "Request timed out")
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': generate_html_response(False, "An unexpected error occurred")
        }
