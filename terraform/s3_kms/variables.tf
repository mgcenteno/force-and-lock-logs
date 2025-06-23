#------------------------------------------------#
# Variables used to pass values to our S3 Bucket #
#------------------------------------------------#

variable "bucket_name" {
  description = "Bucket Name which will be used to our new S3 bucket"
  type        = string
}

variable "organization" {
  description = "AWS Organizations where will be deployed this tool"
  type        = string
}

#-----------------------------------------------#
# Variables used to pass values to our KMS Keys #
#-----------------------------------------------#

variable "kms_description" {
  description = "(Optional) The description of the key as viewed in AWS console"
  type        = string
}

variable "deletion_window_in_days" {
  description = "(Optional) The waiting period, specified in number of days. After the waiting period ends, AWS KMS deletes the KMS key. If you specify a value, it must be between 7 and 30, inclusive. If you do not specify a value, it defaults to 30"
  type        = number
  default     = 30
}

variable "kms_key_rotation" {
  description = "(Optional) The description of the key as viewed in AWS console"
  type        = string
  default     = true
}

variable "deployment_regions" {
  description = "AWS Regions where this resources will be deployed"
  type = list(string)
}

#----------------------#
# Common use variables #
#----------------------#

variable "tags" {
  type = map(string)
  default = {
    "Name"          = "Force and Lock Logs"
    "Environment"   = "Production"
    "Product"       = "Force and Lock Logs"
    "Owner"         = "CloudSecurity"
    "Team"          = "CloudSecurity"
    "Requester"     = "CloudSecurity"
    "IACRepository" = "https://github.com/mgcenteno/force-and-lock-logs"
    "Deploy"        = "Terraform"
    "Organization"  = "Own"
  }
}