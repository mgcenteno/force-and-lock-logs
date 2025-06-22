#---------------------------------------#
# Terraform Backend stored in Amazon S3 #
#---------------------------------------#

terraform {
  backend "s3" {
    bucket       = "s3bkt-force-and-lock-logs-terraform-state"
    key          = "terraform_cloudformation_global.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}