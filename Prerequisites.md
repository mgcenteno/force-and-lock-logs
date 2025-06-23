# What we need to deploy FALL?

To be able to deploy this solution, you should replace at least, the following values with your values:

**Within each Terraform Module:**

* **Define your Terraform Providers**.
* **Required tags**: *List of tags that you want to add into Terraform Resources.*

-----------------------------------------------------------------------------------------------------

**Within terraform/cloudformation_global:**
* **target_id**: *Where to deploy the StackInstance.*
* **deployment_regions**: *AWS Regions where this resources will be deployed.*
* **failure_tolerance_count**: *The number of accounts, per Region, for which this operation can fail before AWS CloudFormation stops the operation in that Region (Optionally)*
* **max_concurrent_count**: *The maximum number of accounts in which to perform this operation at one time (Optionally)*

-----------------------------------------------------------------------------------------------------

**Within terraform/cloudformation_regional:**
* **region_order**: *The order of the Regions in where you want to perform the stack operation (Optionally).*
* **target_id**: *Where to deploy the StackInstance.*
* **deployment_regions (Should be the same as your Region Providers)**: *AWS Regions where this resources will be deployed.*
* **failure_tolerance_count (Optionally)**
* **max_concurrent_count (Optionally)**

-----------------------------------------------------------------------------------------------------

**Within terraform/s3_kms:**
* **organization**: *AWS Organizations where will be deployed this tool.*
* **bucket_name (Optionally)**: *Bucket Name which will be used to our new S3 bucket.*
* **deployment_regions (Should be the same as your Region Providers)**: *AWS Regions where this resources will be deployed.*

-----------------------------------------------------------------------------------------------------

**Within terraform/scp:**
* **target_ids**: *Account, Organizational Unit or Root Account where the Service Control Policies apply and therefore, where the restrictions will apply.*

-----------------------------------------------------------------------------------------------------

**Within templates/global_resources_stackset_fall.yaml:**
* *Not necessary, at least you want to change the naming convention of the IAM Roles and IAM Policies, but if you do it, you should modify the same parameter in "regional_resources_stackset_fall.yaml".*


-----------------------------------------------------------------------------------------------------

**Within templates/regional_resources_stackset_fall.yaml:**
* **Organization**: *AWS Organization Name used as part of the Bucket Name where Lambda get the .Zip files.*
* **Webhook**: *Webhook where the FALL Notifications will be send it.*
* **LogGroupPrefix**: *Prefix Name which will be part of the CloudWatch Log Group name to store VPC Flow Logs (Optionally).*
* **RetentionDays**: *Define how much time the logs will be stored in CloudWatch Log Group.*
* **MemorySize**: *RAM Memory used by Lambda Functions.*
* **Timeout**: *Lambda Function Execution Time.*
* **TransitionInDays**: *This value is used in the Amazon S3 Lifecycle Rule to move the log files to another S3 Storage Class.*
* **StorageClass**: *Amazon S3 Storage Class where the log files will be moved after the TransitionInDays value.*
* **ExpirationInDays**: *This value defines when the S3 Objects Log Files will be deleted in the Logging S3 Bucket.*

-----------------------------------------------------------------------------------------------------

**Within lambda_code/enablecloudfrontstandardlogsv2.py:**

* **elb_account_ids**: *To know the values that you need to use here, you can check this link: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/enable-access-logging.html.*