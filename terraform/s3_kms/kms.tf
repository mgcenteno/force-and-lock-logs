#----------------------------------------------------------------------------------------#
# Creation of a KMS Key used to perform encrypt/decrypt operations on Primary AWS Region #
#----------------------------------------------------------------------------------------#

resource "aws_kms_key" "force_and_lock_logs" {
  provider = aws.primary
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
  provider = aws.primary
  name          = "alias/kmskey-force-and-lock-logs-${data.aws_region.current.name}-${var.organization}"
  target_key_id = aws_kms_key.force_and_lock_logs.id
}


#------------------------------------------------------------------------------------------#
# Creation of a KMS Key used to perform encrypt/decrypt operations on Secondary AWS Region #
#------------------------------------------------------------------------------------------#

resource "aws_kms_key" "force_and_lock_logs" {
  provider = aws.secondary
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
  provider = aws.secondary
  name          = "alias/kmskey-force-and-lock-logs-${data.aws_region.current.name}-${var.organization}"
  target_key_id = aws_kms_key.force_and_lock_logs.id
}