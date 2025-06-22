#----------------------------------------------------------------------------------#
# IAM Role used for our StackSet Deployment in the Delegated Administrator Account #
#----------------------------------------------------------------------------------#

data "aws_iam_policy_document" "AWSCloudFormationStackSetAdministrationRole_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      identifiers = ["cloudformation.amazonaws.com"]
      type        = "Service"
    }
  }
}

data "aws_iam_role" "AWSCloudFormationStackSetAdministrationRole" {
  name = "AWSCloudFormationStackSetAdministrationRole"
}


#--------------------------------------------#
# CloudFormation Template used as a StackSet #
#--------------------------------------------#

resource "aws_cloudformation_stack_set" "force_and_lock_logs" {
  name             = "regional-resources-${var.cf_stackset_name}"
  description      = "CloudFormation Stack used to deploy FALL (Force and Lock Logs) regional resources, this means Lambda, Event-Bridge, and other resources that supports Multi-Region Deployment of FALL"
  permission_model = "SERVICE_MANAGED"

  capabilities = ["CAPABILITY_NAMED_IAM"]

  auto_deployment {
    enabled                          = true
    retain_stacks_on_account_removal = false
  }

  operation_preferences {
    failure_tolerance_count = var.failure_tolerance_count
    max_concurrent_count    = var.max_concurrent_count
    region_order            = ["us-east-1", "sa-east-1"]
  }

  template_body = data.local_file.stackset_template.content

  tags = var.tags
}

data "local_file" "stackset_template" {
  filename = "${path.module}/../../templates/regional_resources_stackset_fall.yaml"
}

locals {
  template_hash = sha256(data.local_file.stackset_template.content)
}

#-------------------------------------------------------------------#
# IAM Role used for our Stack Instances in each AWS Member Accounts #
#-------------------------------------------------------------------#

data "aws_iam_policy_document" "AWSCloudFormationStackSetAdministrationRole_ExecutionPolicy" {
  statement {
    actions   = ["sts:AssumeRole"]
    effect    = "Allow"
    resources = data.aws_iam_role.AWSCloudFormationStackSetAdministrationRole.name
  }
}

resource "aws_iam_role_policy" "AWSCloudFormationStackSetAdministrationRole_ExecutionPolicy" {
  name   = "ExecutionPolicy"
  policy = data.aws_iam_policy_document.AWSCloudFormationStackSetAdministrationRole_ExecutionPolicy.json
  role   = data.aws_iam_role.AWSCloudFormationStackSetAdministrationRole.name
}

#----------------------------------------------------------#
# Deploy Regional Resources at the AWS Organizations Level #
#----------------------------------------------------------#

resource "aws_cloudformation_stack_set_instance" "regional_resources_fall_org" {
  for_each        = toset(var.deployment_regions)
  stack_set_name = aws_cloudformation_stack_set.force_and_lock_logs.name

  deployment_targets {
    organizational_unit_ids = ["${var.target_id}"]
  }

  stack_set_instance_region  = each.key

}

#-----------------------------------------------------------------------------#
# Deploy Regional Resources within the root account itself #
#-----------------------------------------------------------------------------#

resource "aws_cloudformation_stack" "regional_resources_fall_root_org" {
  provider = aws.virginia
  name = "regional-resources-${var.cf_stackset_name}"
  capabilities = ["CAPABILITY_NAMED_IAM"]

  template_body = data.local_file.stackset_template.content

  tags = var.tags
}