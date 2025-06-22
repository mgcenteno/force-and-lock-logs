#------------------------------------------------------------------#
# Creation of a KMS Key used to perform encrypt/decrypt operations #
#------------------------------------------------------------------#

resource "aws_kms_key" "force_and_lock_logs" {
  for_each = toset(var.deployment_regions)
  description             = var.kms_description
  deletion_window_in_days = var.deletion_window_in_days
  enable_key_rotation     = var.kms_key_rotation

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AllowRootAccount",
        Effect = "Allow",
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        },
        Action   = "kms:*",
        Resource = "*"
      },
      {
        Sid    = "AllowLambdaCloudFormationAccess",
        Effect = "Allow",
        Principal = {
          Service = [
            "cloudformation.amazonaws.com",
            "lambda.amazonaws.com"
          ]
        },
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ],
        Resource = "*",
        Condition = {
          StringEquals = {
            "aws:SourceOrgID" = "${data.aws_organizations_organization.organization.id}"
          }
        }
      },
      {
        Sid       = "AllowStackSetExecRolesFromAnyAccount",
        Effect    = "Allow",
        Principal = "*",
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ],
        Resource = "*",
        Condition = {
          StringEquals = {
            "aws:PrincipalOrgID" = "${data.aws_organizations_organization.organization.id}"
          },
          ArnLike = {
            "aws:PrincipalArn" : "arn:aws:iam::*:role/stacksets-exec-*"
          }
        }
      }
    ]
  })
}

resource "aws_kms_alias" "force_and_lock_logs" {
  for_each = toset(var.deployment_regions)
  name          = "alias/kmskey-force-and-lock-logs-${each.key}-${var.organization}"
  target_key_id = aws_kms_key.force_and_lock_logs[each.key].id
}
