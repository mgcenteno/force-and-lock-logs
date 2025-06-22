terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.0.0"
    }
  }
}

provider "aws" {
  alias  = "virginia"
  region = "us-east-1"
}

provider "aws" {
  alias  = "sao_paulo"
  region = "sa-east-1"
}

locals {
  region_provider_map = {
    "us-east-1" = aws.virginia
    "sa-east-1" = aws.sao_paulo
  }
}
