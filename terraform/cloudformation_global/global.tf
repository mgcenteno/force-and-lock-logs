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

resource "aws_iam_role" "AWSCloudFormationStackSetAdministrationRole" {
  assume_role_policy = data.aws_iam_policy_document.AWSCloudFormationStackSetAdministrationRole_assume_role_policy.json
  name               = "AWSCloudFormationStackSetAdministrationRole"
}

#-------------------------------------------------------------------#
# IAM Role used for our Stack Instances in each AWS Member Accounts #
#-------------------------------------------------------------------#

data "aws_iam_policy_document" "AWSCloudFormationStackSetAdministrationRole_ExecutionPolicy" {
  statement {
    actions   = ["sts:AssumeRole"]
    effect    = "Allow"
    resources = ["arn:aws:iam::*:role/${aws_cloudformation_stack_set.global_resources_fall.execution_role_name}"]
  }
}

resource "aws_iam_role_policy" "AWSCloudFormationStackSetAdministrationRole_ExecutionPolicy" {
  name   = "ExecutionPolicy"
  policy = data.aws_iam_policy_document.AWSCloudFormationStackSetAdministrationRole_ExecutionPolicy.json
  role   = aws_iam_role.AWSCloudFormationStackSetAdministrationRole.name
}


#--------------------------------------------#
# CloudFormation Template used as a StackSet #
#--------------------------------------------#

resource "aws_cloudformation_stack_set" "global_resources_fall" {
  name             = "Global-Resources-${var.cf_stackset_name}"
  description      = "CloudFormation Stack used to deploy FALL (Force and Lock Logs) global resources, this means IAM resources that only lives within US-EAST-1, this is useful to avoid errors in a Multi-Region Deployment of FALL"
  permission_model = "SERVICE_MANAGED"

  capabilities = ["CAPABILITY_NAMED_IAM"]

  auto_deployment {
    enabled                          = true
    retain_stacks_on_account_removal = false
  }

  operation_preferences {
    failure_tolerance_count = var.failure_tolerance_count
    max_concurrent_count    = var.max_concurrent_count
  }

  template_body = data.local_file.stackset_template.content

  tags = var.tags
}

data "local_file" "stackset_template" {
  filename = "${path.module}/../../templates/global_resources_stackset_fall.yaml"
}

locals {
  template_hash = sha256(data.local_file.stackset_template.content)
}


#--------------------------------------------------------------#
# Deploy Global Resources (IAM) at the AWS Organizations Level #
#--------------------------------------------------------------#

resource "aws_cloudformation_stack_set_instance" "global_resources_fall_org" {
  for_each       = toset(var.deployment_regions)
  stack_set_name = aws_cloudformation_stack_set.global_resources_fall.name

  deployment_targets {
    organizational_unit_ids = ["${var.target_id}"]
  }

}

#-------------------------------------------------------#
# Deploy Global Resources (IAM) within the root account #
#-------------------------------------------------------#

resource "aws_cloudformation_stack" "global_resources_fall_root_org" {
  provider     = aws.virginia
  name         = "global-resources-${var.cf_stackset_name}"
  capabilities = ["CAPABILITY_NAMED_IAM"]

  template_body = data.local_file.stackset_template.content

  tags = var.tags
}