
import json
import os
import boto3
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

def generate_token():
    return base64.b64encode(os.urandom(32)).decode('utf-8')

def get_signing_secret():
    try:
        secrets = boto3.client('secretsmanager')
        response = secrets.get_secret_value(
            SecretId=os.environ['SIGNING_SECRET_ARN']
        )
        secret_dict = json.loads(response['SecretString'])
        return secret_dict['secret']
    except ClientError as e:
        print(f"Error retrieving secret: {str(e)}")
        raise

def sign_token(token, timestamp):
    try:
        secret = get_signing_secret()
        message = f"{token}:{timestamp}"
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    except Exception as e:
        print(f"Error signing token: {str(e)}")
        raise

def create_approval_email(token, timestamp, expiration, signature):
    base_url = os.environ['MEMBER_API_ENDPOINT']
    params = {
        'token': token,
        'signature': signature,
        'timestamp': timestamp
    }
    encoded_params = urllib.parse.urlencode(params)
    
    approval_link = f"https://{base_url}/approve?{encoded_params}"
    rejection_link = f"https://{base_url}/reject?{encoded_params}"

    message_parts = [
        'PATCHING APPROVAL REQUEST',
        '========================',
        '',
        'A new patching request requires your review and approval.',
        '',
        'APPROVAL ACTIONS',
        '--------------',
        'To APPROVE patching, click or copy/paste this link:',
        f'{approval_link}',
        '',
        'To REJECT patching, click or copy/paste this link:',
        f'{rejection_link}',
        '',
        'ADDITIONAL INFORMATION',
        '--------------------',
        f'Request ID: {token}',
        f'Submitted: {timestamp}',
        f'Expires: {expiration}',
        '',
        'This is an automated message. Please do not reply to this email.'
    ]
    return '\n'.join(message_parts)

def create_rejection_email(token, timestamp):
    message_parts = [
        'PATCHING REQUEST REJECTED',
        '========================',
        '',
        'Customer has rejected the patching request.',
        '',
        'REJECTION DETAILS',
        '----------------',
        'Customer rejected patching at this time.',
        '',
        'ADDITIONAL INFORMATION',
        '--------------------',
        f'Request ID: {token}',
        f'Rejection Date: {timestamp}',
        '',
        'This is an automated message. Please do not reply to this email.'
    ]
    return '\n'.join(message_parts)

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        token = generate_token()
        timestamp = datetime.utcnow().isoformat()
        expiration = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        signature = sign_token(token, timestamp)
        
        sts = boto3.client('sts')
        role_arn = f"arn:aws:iam::{os.environ['MEMBER_ACCOUNT']}:role/{os.environ['MEMBER_STACK_NAME']}-cross-account-dynamodb-role"
        
        try:
            assumed_role = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName="CrossAccountDynamoDBAccess"
            )
        except ClientError as e:
            print(f"Error assuming role {role_arn}: {str(e)}")
            raise

        dynamodb = boto3.client(
            'dynamodb',
            region_name=os.environ['DEPLOYMENT_REGION'],
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken']
        )
        
        try:
            dynamodb.put_item(
                TableName=os.environ['DYNAMODB_TABLE'],
                Item={
                    'token': {'S': token},
                    'status': {'S': 'PENDING'},
                    'expiration': {'S': expiration},
                    'created_at': {'S': timestamp}
                }
            )
        except ClientError as e:
            print(f"DynamoDB error: {str(e)}")
            raise

        message = create_approval_email(token, timestamp, expiration, signature)
        topic_arn = os.environ['SNS_TOPIC_ARN']
        subject = 'Action Required: Patching Approval Request'
        
        sns = boto3.client('sns', region_name=os.environ['DEPLOYMENT_REGION'])
        try:
            sns.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject=subject
            )
        except ClientError as e:
            print(f"SNS error: {str(e)}")
            raise
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Request processed successfully',
                'token': token
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }
