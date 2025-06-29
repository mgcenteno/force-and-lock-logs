#------------------------------------------------------------------------------------------#
# This S3 Bucket will be used to store Lambda Function package files on Primary AWS Region #
#------------------------------------------------------------------------------------------#

resource "aws_s3_bucket" "force_and_lock_logs_primary" {
  provider = aws.primary
  bucket   = "${var.bucket_name}-${data.aws_region.primary.name}-${var.organization}"

  tags     = var.tags
}

#---------------------------------#
# Enabling S3 Block Public Access #
#---------------------------------#

resource "aws_s3_bucket_public_access_block" "force_and_lock_logs_primary" {
  provider = aws.primary
  bucket = aws_s3_bucket.force_and_lock_logs_primary.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

}

#-----------------------------#
# Enabling Encryption at-rest #
#-----------------------------#

resource "aws_s3_bucket_server_side_encryption_configuration" "force_and_lock_logs_primary" {
  provider = aws.primary
  bucket = aws_s3_bucket.force_and_lock_logs_primary.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.force_and_lock_logs_primary.arn
      sse_algorithm     = "aws:kms"
    }
  }

}

#--------------------------------#
# Enabling Encryption in-transit #
#--------------------------------#

resource "aws_s3_bucket_policy" "force_and_lock_logs_primary" {
  provider = aws.primary
  bucket = aws_s3_bucket.force_and_lock_logs_primary.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "DenyUnencryptedRequests",
        Effect    = "Deny",
        Principal = "*",
        Action    = ["s3:PutObject"],
        Resource  = "${aws_s3_bucket.force_and_lock_logs_primary.arn}/*",
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid    = "AllowLambdaCloudFormationAccess",
        Effect = "Allow",
        Principal = {
          Service = ["lambda.amazonaws.com", "cloudformation.amazonaws.com"]
        },
        Action   = ["s3:GetObject", "s3:GetObjectVersion"],
        Resource = "${aws_s3_bucket.force_and_lock_logs_primary.arn}/*",
        Condition = {
          StringEquals = {
            "aws:SourceOrgID" = "${data.aws_organizations_organization.organization.id}"
          }
        }
      },
      {
        Sid       = "AllowLambdaExecutionRoleWithConditions",
        Effect    = "Allow",
        Principal = "*",
        Action    = ["s3:GetObject", "s3:GetObjectVersion"],
        Resource  = "${aws_s3_bucket.force_and_lock_logs_primary.arn}/*",
        Condition = {
          StringEquals = {
            "aws:PrincipalOrgID" = "${data.aws_organizations_organization.organization.id}"
          },
          "ArnLike" = {
            "aws:PrincipalArn" = "arn:aws:iam::*:role/stacksets-exec-*"
          }
        }
      }
    ]
  })
}



#--------------------------------------------------------------------------------------------#
# This S3 Bucket will be used to store Lambda Function package files on Secondary AWS Region #
#--------------------------------------------------------------------------------------------#

resource "aws_s3_bucket" "force_and_lock_logs_secondary" {
  provider = aws.secondary
  bucket   = "${var.bucket_name}-${data.aws_region.secondary.name}-${var.organization}"

  tags     = var.tags
}

#---------------------------------#
# Enabling S3 Block Public Access #
#---------------------------------#

resource "aws_s3_bucket_public_access_block" "force_and_lock_logs_secondary" {
  provider = aws.secondary
  bucket = aws_s3_bucket.force_and_lock_logs_secondary.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

}

#-----------------------------#
# Enabling Encryption at-rest #
#-----------------------------#

resource "aws_s3_bucket_server_side_encryption_configuration" "force_and_lock_logs_secondary" {
  provider = aws.secondary
  bucket = aws_s3_bucket.force_and_lock_logs_secondary.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.force_and_lock_logs_secondary.arn
      sse_algorithm     = "aws:kms"
    }
  }

}

#--------------------------------#
# Enabling Encryption in-transit #
#--------------------------------#

resource "aws_s3_bucket_policy" "force_and_lock_logs_secondary" {
  provider = aws.secondary
  bucket = aws_s3_bucket.force_and_lock_logs_secondary.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "DenyUnencryptedRequests",
        Effect    = "Deny",
        Principal = "*",
        Action    = ["s3:PutObject"],
        Resource  = "${aws_s3_bucket.force_and_lock_logs_secondary.arn}/*",
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid    = "AllowLambdaCloudFormationAccess",
        Effect = "Allow",
        Principal = {
          Service = ["lambda.amazonaws.com", "cloudformation.amazonaws.com"]
        },
        Action   = ["s3:GetObject", "s3:GetObjectVersion"],
        Resource = "${aws_s3_bucket.force_and_lock_logs_secondary.arn}/*",
        Condition = {
          StringEquals = {
            "aws:SourceOrgID" = "${data.aws_organizations_organization.organization.id}"
          }
        }
      },
      {
        Sid       = "AllowLambdaExecutionRoleWithConditions",
        Effect    = "Allow",
        Principal = "*",
        Action    = ["s3:GetObject", "s3:GetObjectVersion"],
        Resource  = "${aws_s3_bucket.force_and_lock_logs_secondary.arn}/*",
        Condition = {
          StringEquals = {
            "aws:PrincipalOrgID" = "${data.aws_organizations_organization.organization.id}"
          },
          "ArnLike" = {
            "aws:PrincipalArn" = "arn:aws:iam::*:role/stacksets-exec-*"
          }
        }
      }
    ]
  })
}