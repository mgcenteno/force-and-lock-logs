data "aws_caller_identity" "current" {}

data "aws_organizations_organization" "organization" {}

data "aws_region" "current" {}

data "aws_region" "primary" {
  provider = aws.primary
}

data "aws_region" "secondary" {
  provider = aws.secondary
}
