import boto3
import os
import json
import urllib.request

logs_client = boto3.client('logs')
ec2_client = boto3.client('ec2')

# Retrieve the corresponding values from the Lambda Environment Variables (Defined in CloudFormation Template)

LOG_GROUP_PREFIX = os.environ.get("LOG_GROUP_PREFIX", "/vpc-flow-logs/")    # Used as part of the name of the CloudWatch Log Group.
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))                # Used to define the retention of logs in the CloudWatch Log Group.
KMS_KEY_ARN = os.environ.get("KMS_KEY_ARN")                                 # Used to encrypt the CloudWatch Log Group where our VPC Flow logs will be stored.
FLOW_LOG_ROLE_ARN = os.environ.get("FLOW_LOG_ROLE_ARN")                     # IAM Role used in the configuration of the VPC Flow Logs creation, is NOT the same as the Lambda uses to perform their tasks.
WEBHOOK_GOOGLE_CHAT = os.environ.get("WEBHOOK_GOOGLE_CHAT")                 # Used to forward our notification status to a Google Chat Space.

"""
Principal function or entry point to start the execution of Lambda where first of all we extract the VPC_ID parameter from CloudTrail Event
We validate the presence of the ExcludeLogging tag, we defined the CloudWatch Log Group name and after that create it with some parameters like
RETENTION_DAYS and KMS_KEY_ARN, and finally send a Google Chat Notification.
"""

def lambda_handler(event, context):
    detail = event.get("detail", {})
    vpc_id = detail.get("responseElements", {}).get("vpc", {}).get("vpcId")
    account_id = detail.get("userIdentity", {}).get("accountId", "Unknown Account")
    region = detail.get("awsRegion", "Invalid Region")
    principal = detail.get("userIdentity", {}).get("arn", "Unknown")

    if not vpc_id:
        print("No VPC ID found in the CloudTrail Event")
        return

    if not KMS_KEY_ARN or not FLOW_LOG_ROLE_ARN or not WEBHOOK_GOOGLE_CHAT:
        raise Exception("Missing required environment variables")

    log_group_name = f"{LOG_GROUP_PREFIX}{vpc_id}"

    try:
        tags_response = ec2_client.describe_tags(
            Filters=[
                {'Name': 'resource-id', 'Values': [vpc_id]},
                {'Name': 'resource-type', 'Values': ['vpc']}
            ]
        )

        tags = {tag['Key'].lower(): tag['Value'].lower() for tag in tags_response.get('Tags', [])}
        exclude_logging = tags.get("excludelogging", "false")

        if exclude_logging == "true":
            print(f"VPC {vpc_id} has the tag ExcludeLogging=True. Skipping creation of VPC Flow Logs.")
            send_google_chat_message(
                WEBHOOK_GOOGLE_CHAT, vpc_id, account_id, region,
                log_group_name=None,
                success=False,
                excluded_reason="Tag ExcludeLogging=True",
                principal=principal
            )
            return

        try:
            logs_client.create_log_group(
                logGroupName=log_group_name,
                kmsKeyId=KMS_KEY_ARN
            )
            print(f"Created log group {log_group_name} with KMS key")
        except logs_client.exceptions.ResourceAlreadyExistsException:
            print(f"Log group already exists: {log_group_name}")

        logs_client.put_retention_policy(
            logGroupName=log_group_name,
            retentionInDays=RETENTION_DAYS
        )

        response = ec2_client.create_flow_logs(
            ResourceIds=[vpc_id],
            ResourceType='VPC',
            TrafficType='ALL',
            LogGroupName=log_group_name,
            DeliverLogsPermissionArn=FLOW_LOG_ROLE_ARN,
            MaxAggregationInterval=60
        )

        print(f"Created Flow Log: {response}")
        send_google_chat_message(WEBHOOK_GOOGLE_CHAT, vpc_id, account_id, region, log_group_name, success=True, principal=principal)

        return {
            'statusCode': 200,
            'body': f'VPC Flow Log created for VPC {vpc_id}'
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        send_google_chat_message(
            WEBHOOK_GOOGLE_CHAT, vpc_id, account_id, region,
            log_group_name=log_group_name,
            success=False,
            error_message=str(e),
            principal=principal
        )
        return {
            'statusCode': 500,
            'body': f'Failed to create VPC Flow Log for VPC {vpc_id}'
        }

# This function is used to send Google Chat messages to indicate the status logging

def send_google_chat_message(WEBHOOK_GOOGLE_CHAT, vpc_id, account_id, region, log_group_name=None, success=True, error_message=None, excluded_reason=None, principal=None):
    if excluded_reason:
        status_text = "⚠️ VPC Flow Logs was skipped due to ExcludeLogging tag"
    else:
        status_text = "✅ VPC Flow Logs successfully enabled" if success else "❌ Error enabling VPC Flow Logs"

    card_payload = {
        "cards": [
            {
                "header": {
                    "title": status_text,
                    "subtitle": f"VPC ID: {vpc_id}",
                    "imageUrl": "https://miro.medium.com/v2/resize:fit:320/1*w8V1ODjFtZzsKLWklIx5SQ.png",
                    "imageStyle": "AVATAR"
                },
                "sections": [
                    {
                        "widgets": [
                            {"keyValue": {"topLabel": "Account ID", "content": account_id}},
                            {"keyValue": {"topLabel": "AWS Region", "content": region}},
                            {"keyValue": {"topLabel": "Log Group", "content": log_group_name or "N/A"}},
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
            print(f"The message was sent to Google Chat with status code: {response.status}")
    except Exception as e:
        print(f"Failed to send message to Google Chat: {e}")
