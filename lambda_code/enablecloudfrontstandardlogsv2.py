import boto3
import os
import json
import logging
import re
import urllib3
import urllib.request
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region = boto3.session.Session().region_name
s3 = boto3.client('s3')
sts = boto3.client('sts')
logs = boto3.client('logs', region_name='us-east-1')
elbv2 = boto3.client('elbv2')
cloudfront = boto3.client('cloudfront')

# Retrieve the corresponding values from the Lambda Environment Variables (Defined in CloudFormation Template)

KMS_KEY_ARN = os.environ['KMS_KEY_ARN']                     # Used to encrypt the S3 Bucket where our CloudFront logs will be stored.
TRANSITION_IN_DAYS = int(os.environ['TRANSITION_IN_DAYS'])  # Used in the Lifecycle Rule of the S3 Bucket.
STORAGE_CLASS = os.environ['STORAGE_CLASS']                 # S3 Storage Class used to send the logs after the days defined in TRANSITION_IN_DAYS variable.
EXPIRATION_IN_DAYS = int(os.environ['EXPIRATION_IN_DAYS'])  # Used to define when the log files will be deleted from our S3 Bucket
WEBHOOK_GOOGLE_CHAT = os.environ.get("WEBHOOK_GOOGLE_CHAT") # Used to forward our notification status to a Google Chat Space.

http = urllib3.PoolManager()

"""
Principal function or entry point to start the execution of Lambda where first of all we extract the DistributionId
We validate the presence of the ExcludeLogging tag, define the S3 Bucket Name for our CloudFront logs, Validate if 
the Distribution ID has already logging enabled by the User to skip the creation of the bucket and avoid an unnecessary 
error message, in case of everything is OK, we create the bucket with the security best practicas and then enable CloudFront
Logging using Delivery Source, Destination and send the notification to administrators via Webhook.
"""

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    distribution_id = ""
    account_id = ""
    bucket_name = ""
    principal_arn = event['detail'].get('userIdentity', {}).get('arn', 'Unknown')

    try:
        distribution_id = event['detail']['responseElements']['distribution']['id']
        account_id = sts.get_caller_identity()["Account"]

        if is_excluded(distribution_id):
            logger.info(f"Exclusion tag found for distribution {distribution_id}, skipping log configuration.")
            send_chat_card(
                distribution_id=distribution_id,
                account_id=account_id,
                bucket_name="(N/A)",
                success=True,
                already_enabled=True,
                exclusion=True,
                principal_arn=principal_arn
            )
            return {"status": "excluded"}

        safe_name = sanitize_name(distribution_id)
        bucket_name = f"s3bkt-access-logging-{safe_name}"
        dest_name = f"CF-{distribution_id}-{safe_name}"
        source_name = f"CreatedByCloudFront-{distribution_id}"
        resource_arn = f'arn:aws:cloudfront::{account_id}:distribution/{distribution_id}'

        try:
            logs.put_delivery_source(
                name=dest_name,
                resourceArn=resource_arn,
                logType='ACCESS_LOGS'
            )
        except logs.exceptions.ConflictException:
            logger.info(f"Standard Logging v2 already enabled by the user for the Distribution: {distribution_id}")
            send_chat_card(
                distribution_id=distribution_id,
                account_id=account_id,
                bucket_name="(N/A)",
                success=True,
                already_enabled=True,
                principal_arn=principal_arn
            )
            return {"status": "already-enabled"}

        if not bucket_exists(bucket_name):
            create_logging_bucket(bucket_name)

        apply_bucket_policy(bucket_name, account_id, source_name)

        logs.put_delivery_destination(
            name=dest_name,
            outputFormat='json',
            deliveryDestinationConfiguration={
                'destinationResourceArn': f'arn:aws:s3:::{bucket_name}'
            }
        )

        logs.create_delivery(
            deliverySourceName=dest_name,
            deliveryDestinationArn=f'arn:aws:logs:us-east-1:{account_id}:delivery-destination:{dest_name}'
        )

        send_chat_card(
            distribution_id=distribution_id,
            account_id=account_id,
            bucket_name=bucket_name,
            success=True,
            principal_arn=principal_arn
        )

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error: {e}")
        send_chat_card(
            distribution_id=distribution_id,
            account_id=account_id,
            bucket_name=bucket_name,
            success=False,
            error_message=str(e),
            principal_arn=principal_arn
        )
        return {"status": "error", "message": str(e)}

"""
At this stage of the Lambda Execution, we defined the secondary functions which will be used within the lambda_handler
For example all evaluation logic or conditionals evaluated to avoid the creation of unnecesary resources or avoid error messages
"""


# Here we defined the evaluation logic to determine if the created resource has the Tag/Value ExcludeLogging set in True,
# if this is the case we skipped the enabling logging process.


def is_excluded(distribution_id):
    try:
        response = cloudfront.list_tags_for_resource(
            Resource=f'arn:aws:cloudfront::{sts.get_caller_identity()["Account"]}:distribution/{distribution_id}'
        )
        tags = response.get("Tags", {}).get("Items", [])
        for tag in tags:
            if tag.get("Key") == "ExcludeLogging" and tag.get("Value", "").lower() == "true":
                return True
    except Exception as e:
        logger.warning(f"Unable to get tags for distribution {distribution_id}: {e}")
    return False

# This is used to sanitize the name because this value will be used as part of the S3 Bucket name created to store the log files.

def sanitize_name(name):
    return re.sub(r'[^a-zA-Z0-9\-]', '-', name.lower())

# This function is used to validate if previously exists an S3 Bucket with the same name as the bucket what we want to create to avoid an Error Message.

def bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        raise

# Here we create the bucket after successfully passed all the previous conditionals

def create_logging_bucket(bucket_name):
    if region == 'us-east-1':
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )

    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )

    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            'Rules': [{
                'ApplyServerSideEncryptionByDefault': {
                    'SSEAlgorithm': 'aws:kms',
                    'KMSMasterKeyID': KMS_KEY_ARN
                }
            }]
        }
    )

    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={
            'Rules': [{
                'ID': 'LifecycleRuleArchivingAndExpiration',
                'Filter': {'Prefix': ''},
                'Status': 'Enabled',
                'Transitions': [{
                    'Days': TRANSITION_IN_DAYS,
                    'StorageClass': STORAGE_CLASS
                }],
                'Expiration': {'Days': EXPIRATION_IN_DAYS}
            }]
        }
    )

# This function just put the bucket policy that CloudFront Service needs to be able to store logs in an S3 Bucket

def apply_bucket_policy(bucket_name, account_id, source_name):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AWSLogDeliveryWrite",
                "Effect": "Allow",
                "Principal": {
                    "Service": "delivery.logs.amazonaws.com"
                },
                "Action": "s3:PutObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/AWSLogs/{account_id}/CloudFront/*",
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control",
                        "aws:SourceAccount": account_id
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:logs:us-east-1:{account_id}:delivery-source:{source_name}"
                    }
                }
            }
        ]
    }

    s3.put_bucket_policy(
        Bucket=bucket_name,
        Policy=json.dumps(policy)
    )

# This function is used to send Google Chat messages to indicate the status logging

def send_chat_card(distribution_id, account_id, bucket_name, success, error_message=None, already_enabled=False, exclusion=False, principal_arn="Unknown"):
    if exclusion:
        status = "⚠️ CloudFront Logging was skipped due to ExcludeLogging tag"
    elif already_enabled:
        status = "ℹ️ CloudFront Distribution already had Standard Logging v2 enabled"
    else:
        status = "✅ CloudFront Standard Logging v2 successfully enabled" if success else "❌ Error enabling Standard Logging v2"

    card_payload = {
        "cards": [
            {
                "header": {
                    "title": status,
                    "subtitle": f"Distribution ID: {distribution_id}",
                    "imageUrl": "https://mediaresource.sfo2.digitaloceanspaces.com/wp-content/uploads/2024/04/22100513/aws-cloudfront-logo-D475098A98-seeklogo.com.png",
                    "imageStyle": "AVATAR"
                },
                "sections": [
                    {
                        "widgets": [
                            {"keyValue": {"topLabel": "Account ID", "content": account_id}},
                            {"keyValue": {"topLabel": "AWS Region", "content": region}},
                            {"keyValue": {"topLabel": "Target Logging Bucket", "content": bucket_name}},
                            {"textParagraph": {"text": f"Principal: {principal_arn}"}}
                        ]
                    }
                ]
            }
        ]
    }

    if not success and error_message:
        card_payload["cards"][0]["sections"].append({
            "widgets": [
                {"textParagraph": {"text": f"Error: {error_message}"}}
            ]
        })

    data = json.dumps(card_payload).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_GOOGLE_CHAT, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            logger.info(f"The message was sent it to Google Chat with the status code: {response.status}")
    except Exception as e:
        logger.error(f"Failed to send skip message to Google Chat: {e}")