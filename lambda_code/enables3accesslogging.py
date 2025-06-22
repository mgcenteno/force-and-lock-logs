import boto3
import os
import logging
import json
import urllib.request
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
sts = boto3.client('sts')

# Retrieve the corresponding values from the Lambda Environment Variables (Defined in CloudFormation Template)

DEPLOYMENT_REGION = os.environ['DEPLOYMENT_REGION']         # AWS Region where we will deploy the region, allowed option are us-east-1 and sa-east-1
KMS_KEY_ARN = os.environ.get('KMS_KEY_ARN')                 # Used to encrypt the S3 Bucket where our CloudFront logs will be stored.
TRANSITION_IN_DAYS = int(os.environ['TRANSITION_IN_DAYS'])  # Used in the Lifecycle Rule of the S3 Bucket.
STORAGE_CLASS = os.environ['STORAGE_CLASS']                 # S3 Storage Class used to send the logs after the days defined in TRANSITION_IN_DAYS variable.
EXPIRATION_IN_DAYS = int(os.environ['EXPIRATION_IN_DAYS'])  # Used to define when the log files will be deleted from our S3 Bucket
WEBHOOK_GOOGLE_CHAT = os.environ.get("WEBHOOK_GOOGLE_CHAT") # Used to forward our notification status to a Google Chat Space.

"""
Principal function or entry point to start the execution of Lambda where first of all we extract the S3 Bucket Name parameter and then validate the presence of the ExcludeLogging tag,
we validate if the created bucket is an Logging Bucket or not to decide if skip the creation process or continue, if not, we execute different configuration aligned to AWS Security Best Practices
in the new S3 Bucket which will store the Server Access Logs and finally send a Google Chat Notification.
"""

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    created_bucket_name = None
    access_logging_bucket = None
    account_id = sts.get_caller_identity()["Account"]
    principal = event['detail'].get('userIdentity', {}).get('arn', 'Unknown')

    try:
        created_bucket_name = event['detail']['requestParameters']['bucketName']
        logger.info(f"Bucket detected: {created_bucket_name}")

        if created_bucket_name.startswith("s3bkt-access-logging-"):
            logger.info("This S3 Bucket is an Logging Bucket, stop the process to avoid recursive operation.")
            return

        try:
            tag_set = s3.get_bucket_tagging(Bucket=created_bucket_name)['TagSet']
            tags = {tag['Key'].lower(): tag['Value'].lower() for tag in tag_set}
            exclude_logging = tags.get("excludelogging", "false")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                exclude_logging = "false"
            else:
                raise

# Validate the presence of the Tag/Value ExcludeLogging.

        if exclude_logging == "true":
            logger.info(f"Bucket {created_bucket_name} has the tag and value ExcludeLogging=True. Skip logging process.")
            principal = event['detail'].get('userIdentity', {}).get('arn', 'Unknown')
            send_chat_card(
                bucket_name=created_bucket_name,
                account_id=account_id,
                region=DEPLOYMENT_REGION,
                access_logging_bucket=None,
                excluded_reason="Tag ExcludeLogging=True",
                principal=principal
            )
            return

# Validate the new S3 Bucket name and if this already exists or not to continue with CreateBucket API and Security Best Practices.

        access_logging_bucket = f"s3bkt-access-logging-{created_bucket_name}"

        existing_buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]
        if access_logging_bucket not in existing_buckets:
            logger.info(f"Creating S3 Bucket named: {access_logging_bucket}")

            if DEPLOYMENT_REGION == 'us-east-1':
                s3.create_bucket(Bucket=access_logging_bucket)
            else:
                s3.create_bucket(
                    Bucket=access_logging_bucket,
                    CreateBucketConfiguration={'LocationConstraint': DEPLOYMENT_REGION}
                )

            s3.put_bucket_versioning(
                Bucket=access_logging_bucket,
                VersioningConfiguration={'Status': 'Enabled'}
            )

            s3.put_bucket_encryption(
                Bucket=access_logging_bucket,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'aws:kms',
                                'KMSMasterKeyID': KMS_KEY_ARN
                            }
                        }
                    ]
                }
            )

            s3.put_bucket_lifecycle_configuration(
                Bucket=access_logging_bucket,
                LifecycleConfiguration={
                    'Rules': [
                        {
                            'ID': 'LifecycleRuleArchivingAndExpiration',
                            'Prefix': 'logs/',
                            'Status': 'Enabled',
                            'Transitions': [
                                {
                                    'Days': TRANSITION_IN_DAYS,
                                    'StorageClass': STORAGE_CLASS
                                }
                            ],
                            'Expiration': {
                                'Days': EXPIRATION_IN_DAYS
                            }
                        }
                    ]
                }
            )

            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "S3ServerAccessLogsPolicy",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "logging.s3.amazonaws.com"
                        },
                        "Action": ["s3:PutObject"],
                        "Resource": f"arn:aws:s3:::{access_logging_bucket}/logs/*",
                        "Condition": {
                            "ArnLike": {
                                "aws:SourceArn": f"arn:aws:s3:::{created_bucket_name}"
                            },
                            "StringEquals": {
                                "aws:SourceAccount": account_id
                            }
                        }
                    }
                ]
            }

            s3.put_bucket_policy(
                Bucket=access_logging_bucket,
                Policy=json.dumps(bucket_policy)
            )

        s3.put_bucket_logging(
            Bucket=created_bucket_name,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': access_logging_bucket,
                    'TargetPrefix': 'logs/'
                }
            }
        )

        send_chat_card(
            bucket_name=created_bucket_name,
            account_id=account_id,
            region=DEPLOYMENT_REGION,
            access_logging_bucket=access_logging_bucket,
            principal=principal,
            success=True
        )


    except Exception as e:
        logger.error(f"Error: {str(e)}")
        send_chat_card(
            bucket_name=created_bucket_name,
            account_id=account_id,
            region=DEPLOYMENT_REGION,
            access_logging_bucket=access_logging_bucket,
            principal=principal,
            success=False,
            error_message=str(e)
        )
        raise

# This function is used to send Google Chat messages to indicate the status logging

def send_chat_card(bucket_name, account_id, region, access_logging_bucket, success=True, error_message=None, excluded_reason=None, principal=None):
    if excluded_reason:
        status_text = "⚠️ S3 Access Logging was skipped due to ExcludeLogging tag"
    else:
        status_text = "✅ S3 Access Logging successfully enabled" if success else "❌ Error enabling S3 Access Logging"

    card_payload = {
        "cards": [
            {
                "header": {
                    "title": status_text,
                    "subtitle": f"Bucket: {bucket_name}",
                    "imageUrl": "https://d2908q01vomqb2.cloudfront.net/22d200f8670dbdb3e253a90eee5098477c95c23d/2021/08/24/Amazon-S3-icon-ForSocial.jpg",
                    "imageStyle": "AVATAR"
                },
                "sections": [
                    {
                        "widgets": [
                            {"keyValue": {"topLabel": "Account ID", "content": account_id}},
                            {"keyValue": {"topLabel": "AWS Region", "content": region}},
                            {"keyValue": {"topLabel": "Target Logging Bucket", "content": access_logging_bucket or "N/A"}},
                            {"textParagraph": {"text": f"Principal: {principal or 'Unknown'}"}}
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
            logger.info(f"The message was sent to Google Chat with the status code: {response.status}")
    except Exception as e:
        logger.error(f"Failed to send message to Google Chat: {e}")
