import boto3
import os
import json
import logging
import urllib.request
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
elbv2 = boto3.client('elbv2')
sts = boto3.client('sts')

# This variable is used to determine the ELB Owner AWS Account for each AWS Region that we used according to the AWS Documentation.

elb_account_ids = {
    'us-east-1': '127311923021',
    'sa-east-1': '507241528517'
}

# Retrieve the corresponding values from the Lambda Environment Variables (Defined in CloudFormation Template)


KMS_KEY_ARN = os.environ.get('KMS_KEY_ARN')                 # Used to encrypt the S3 Bucket where our ELB Access logs will be stored.
TRANSITION_IN_DAYS = int(os.environ['TRANSITION_IN_DAYS'])  # Used in the Lifecycle Rule of the S3 Bucket.
STORAGE_CLASS = os.environ['STORAGE_CLASS']                 # S3 Storage Class used to send the logs after the days defined in TRANSITION_IN_DAYS variable.
EXPIRATION_IN_DAYS = int(os.environ['EXPIRATION_IN_DAYS'])  # Used to define when the log files will be deleted from our S3 Bucket
WEBHOOK_GOOGLE_CHAT = os.environ.get("WEBHOOK_GOOGLE_CHAT") # Used to forward our notification status to a Google Chat Space.

"""
Principal function or entry point to start the execution of Lambda where first of all we extract the Elastic Load Balancer Name
We validate the presence of the ExcludeLogging tag, we determine what type of ELB the user created because depend on that we need to
execute different configurations in the S3 Bucket which will store the Access Logs. Also we perform some evaluation to validate if the ELB
Previously exists and the corresponding S3 Bucket still exists and reuse it, if not, we create the bucket aligned with AWS Security Best Practices
and send a Google Chat Notification.
"""

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    detail = event['detail']
    region = event['region']
    lb_arn = detail['responseElements']['loadBalancers'][0]['loadBalancerArn']

    lb_description = elbv2.describe_load_balancers(LoadBalancerArns=[lb_arn])['LoadBalancers'][0]
    lb_type = lb_description['Type']
    lb_name = lb_description['LoadBalancerName']

    tags = elbv2.describe_tags(ResourceArns=[lb_arn])['TagDescriptions'][0]['Tags']
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    exclude_logging = tag_dict.get("ExcludeLogging", "").lower() == "true"

    if exclude_logging:
        account_id = sts.get_caller_identity()['Account']
        principal_arn = event['detail'].get('userIdentity', {}).get('principalId', 'Unknown')
        send_skip_notification(lb_name, lb_type, region, account_id, principal_arn, lb_arn)
        logger.info(f"Skipping logging configuration for {lb_name} due to ExcludeLogging tag")
        return

    if lb_type == 'application':
        handle_application_lb(lb_arn, lb_name, region, event)
    elif lb_type == 'network':
        handle_network_lb(lb_arn, lb_name, region, event)
    else:
        logger.info(f"Load Balancer {lb_name} has unsupported type: {lb_type}")

# This function is used to manage the security best practices applied when the user created an Application Load Balancer

def handle_application_lb(lb_arn, lb_name, region, event):
    bucket_name = f"s3bkt-access-logging-{lb_name}"
    error_message = None
    principal_arn = "Unknown"

    try:
        principal_arn = event['detail'].get('userIdentity', {}).get('arn', 'Unknown')

        if not bucket_exists(bucket_name):
            logger.info(f"Bucket {bucket_name} does not exist. Creating...")
            create_logging_bucket(bucket_name, region, type='alb')
            apply_bucket_policy(bucket_name, region, type='alb')
        else:
            logger.info(f"Bucket {bucket_name} already exists. Skipping creation.")

        if is_logging_enabled(lb_arn, bucket_name):
            logger.info(f"Access logging is already enabled for ALB {lb_name}. Skipping configuration.")
        else:
            configure_lb_logging(lb_arn, bucket_name)
            logger.info(f"Access logging enabled for ALB {lb_name}.")

        logging_enabled = True
    except Exception as e:
        logger.error(f"Error configuring logging for ALB {lb_name}: {e}")
        logging_enabled = False
        error_message = str(e)

    my_account_id = sts.get_caller_identity()['Account']
    send_chat_card(lb_name, 'application', region, my_account_id, logging_enabled, bucket_name, principal_arn, error_message)

# This function is used to manage the security best practices applied when the user created an Network Load Balancer

def handle_network_lb(lb_arn, lb_name, region, event):
    bucket_name = f"s3bkt-access-logging-{lb_name}"
    error_message = None
    principal_arn = "Unknown"

    try:
        principal_arn = event['detail'].get('userIdentity', {}).get('arn', 'Unknown')

        if not bucket_exists(bucket_name):
            logger.info(f"Bucket {bucket_name} does not exist. Creating...")
            create_logging_bucket(bucket_name, region, type='nlb')
            apply_bucket_policy(bucket_name, region, type='nlb')
        else:
            logger.info(f"Bucket {bucket_name} already exists. Skipping creation.")

        if is_logging_enabled(lb_arn, bucket_name):
            logger.info(f"Access logging is already enabled for NLB {lb_name}. Skipping configuration.")
        else:
            configure_lb_logging(lb_arn, bucket_name)
            logger.info(f"Access logging enabled for NLB {lb_name}.")

        logging_enabled = True
    except Exception as e:
        logger.error(f"Error configuring logging for NLB {lb_name}: {e}")
        logging_enabled = False
        error_message = str(e)

    my_account_id = sts.get_caller_identity()['Account']
    send_chat_card(lb_name, 'network', region, my_account_id, logging_enabled, bucket_name, principal_arn, error_message)

# This function is used to validate if the S3 Bucket Name that we created using s3bkt-access-logging-${ELB_Name} already exists.

def bucket_exists(bucket_name):
    response = s3.list_buckets()
    buckets = [b['Name'] for b in response['Buckets']]
    return bucket_name in buckets

# At this stage we create the Bucket to store ELB Access Logs with some considerations for example if the AWS Regions is us-east-1 or not.

def create_logging_bucket(bucket_name, region, type):
    create_bucket_params = {
        'Bucket': bucket_name,
        'CreateBucketConfiguration': {'LocationConstraint': region}
    }
    if region == 'us-east-1':
        create_bucket_params.pop('CreateBucketConfiguration')

    s3.create_bucket(**create_bucket_params)

    s3.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={'Status': 'Enabled'}
    )

    if type == 'alb':
        encryption_config = {
            'Rules': [ {
                'ApplyServerSideEncryptionByDefault': {
                    'SSEAlgorithm': 'AES256'
                }
            }]
        }
    elif type == 'nlb':
        if not KMS_KEY_ARN:
            raise Exception("KMS_KEY_ARN environment variable is not set for NLB buckets.")
        encryption_config = {
            'Rules': [ {
                'ApplyServerSideEncryptionByDefault': {
                    'SSEAlgorithm': 'aws:kms',
                    'KMSMasterKeyID': KMS_KEY_ARN
                }
            }]
        }
    else:
        raise Exception(f"Unsupported bucket type for encryption configuration: {type}")

    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration=encryption_config
    )

    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={
            'Rules': [ {
                'ID': 'LifecycleRuleArchivingAndExpiration',
                'Filter': {'Prefix': ''},
                'Status': 'Enabled',
                'Transitions': [ {
                    'Days': TRANSITION_IN_DAYS,
                    'StorageClass': STORAGE_CLASS
                }],
                'Expiration': {'Days': EXPIRATION_IN_DAYS}
            }]
        }
    )

# This functions apply the bucket policy itself depending of the ELB type.

def apply_bucket_policy(bucket_name, region, type):
    elb_account_id = elb_account_ids.get(region)
    if not elb_account_id:
        raise Exception(f"Unsupported region for ELB logging: {region}")

    my_account_id = sts.get_caller_identity()['Account']

    if type == 'alb':
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{elb_account_id}:root"},
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/AWSLogs/{my_account_id}/*"
                },
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "delivery.logs.amazonaws.com"},
                    "Action": "s3:GetBucketAcl",
                    "Resource": f"arn:aws:s3:::{bucket_name}"
                }
            ]
        }
    elif type == 'nlb':
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "delivery.logs.amazonaws.com"},
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/AWSLogs/{my_account_id}/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-acl": "bucket-owner-full-control",
                            "aws:SourceAccount": [my_account_id]
                        },
                        "ArnLike": {
                            "aws:SourceArn": [f"arn:aws:logs:{region}:{my_account_id}:*"]
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "delivery.logs.amazonaws.com"},
                    "Action": "s3:GetBucketAcl",
                    "Resource": f"arn:aws:s3:::{bucket_name}",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceAccount": [my_account_id]
                        },
                        "ArnLike": {
                            "aws:SourceArn": [f"arn:aws:logs:{region}:{my_account_id}:*"]
                        }
                    }
                }
            ]
        }
    else:
        raise Exception(f"Unsupported Load Balancer type for policy generation: {type}")

    s3.put_bucket_policy(
        Bucket=bucket_name,
        Policy=json.dumps(policy)
    )

# This function enables the Access Logs in the Elastic Load Balancer.

def configure_lb_logging(lb_arn, bucket_name):
    elbv2.modify_load_balancer_attributes(
        LoadBalancerArn=lb_arn,
        Attributes=[
            {
                'Key': 'access_logs.s3.enabled',
                'Value': 'true'
            },
            {
                'Key': 'access_logs.s3.bucket',
                'Value': bucket_name
            }
        ]
    )
    logger.info(f"Access logging enabled for LB {lb_arn} to bucket {bucket_name}")

# This functions checks if the ELB has already a Logging enabled by the user after to try to enable it.

def is_logging_enabled(lb_arn, expected_bucket_name):
    try:
        attributes = elbv2.describe_load_balancer_attributes(LoadBalancerArn=lb_arn)['Attributes']
        logging_enabled = any(attr['Key'] == 'access_logs.s3.enabled' and attr['Value'] == 'true' for attr in attributes)
        logging_bucket_matches = any(attr['Key'] == 'access_logs.s3.bucket' and attr['Value'] == expected_bucket_name for attr in attributes)
        return logging_enabled and logging_bucket_matches
    except Exception as e:
        logger.warning(f"It was not possible to validate if the Access Logs are enabled in the ELB: {lb_arn}: {e}")
        return False

# This function is used to send Google Chat messages to indicate the status logging

def send_chat_card(lb_name, lb_type, region, my_account_id, logging_enabled, bucket_name, principal_arn, error_message=None):
    status = "✅ Access Logs successfully enabled" if logging_enabled else "❌ Error trying to enable Access Logs"

    card_payload = {
        "cards": [
            {
                "header": {
                    "title": status,
                    "subtitle": f"Load Balancer: {lb_name}",
                    "imageUrl": "https://help.sumologic.com/img/integrations/amazon-aws/elb.png",
                    "imageStyle": "AVATAR"
                },
                "sections": [
                    {
                        "widgets": [
                            {"keyValue": {"topLabel": "Load Balancer Type", "content": lb_type}},
                            {"keyValue": {"topLabel": "Account ID", "content": my_account_id}},
                            {"keyValue": {"topLabel": "AWS Region", "content": region}},
                            {"keyValue": {"topLabel": "Target Logging Bucket", "content": bucket_name}},
                            {"textParagraph": {"text": f"Principal: {principal_arn}"}}
                        ]
                    }
                ]
            }
        ]
    }

    if not logging_enabled and error_message:
        card_payload["cards"][0]["sections"].append({
            "widgets": [
                {"textParagraph": {"text": f"Error: {error_message}"}}
            ]
        })

    data = json.dumps(card_payload).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_GOOGLE_CHAT, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            logger.info(f"Message sent using Google Chat with the status code: {response.status}")
    except Exception as e:
        logger.error(f"It was not possible to send the message using Google Chat: {e}")

def send_skip_notification(lb_name, lb_type, region, account_id, principal_arn, lb_arn):
    card_payload = {
        "cards": [
            {
                "header": {
                    "title": "⚠️ Load Balancer Logging was skipped due to ExcludeLogging tag",
                    "subtitle": f"Load Balancer: {lb_name}",
                    "imageUrl": "https://help.sumologic.com/img/integrations/amazon-aws/elb.png",
                    "imageStyle": "AVATAR"
                },
                "sections": [
                    {
                        "widgets": [
                            {"keyValue": {"topLabel": "Load Balancer Type", "content": lb_type}},
                            {"keyValue": {"topLabel": "Account ID", "content": account_id}},
                            {"keyValue": {"topLabel": "AWS Region", "content": region}},
                            {"keyValue": {"topLabel": "Target Logging Bucket", "content": "(N/A)"}},
                            {"keyValue": {"topLabel": "Principal", "content": principal_arn}},
                        ]
                    }
                ]
            }
        ]
    }

    data = json.dumps(card_payload).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_GOOGLE_CHAT, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            logger.info(f"The message was sent it to Google Chat with the status code: {response.status}")
    except Exception as e:
        logger.error(f"Failed to send skip message to Google Chat: {e}")
