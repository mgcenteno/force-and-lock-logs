variable "cf_stackset_name" {
  description = "CloudFormation StackSet Name"
  type        = string
}

variable "failure_tolerance_count" {
  description = "(Optional) The number of accounts, per Region, for which this operation can fail before AWS CloudFormation stops the operation in that Region"
  type        = number
}

variable "max_concurrent_count" {
  description = "(Optional) The maximum number of accounts in which to perform this operation at one time"
  type        = number
}

variable "region_order" {
  description = "(Optional) The order of the Regions in where you want to perform the stack operation"
  type        = list(string)
}

variable "target_id" {
  description = "Where to deploy the StackInstance"
  type        = string
}

variable "deployment_regions" {
  type = list(string)
}

variable "tags" {
  type = map(string)
  default = {
    "Name"             = "Force and Lock Logs"
    "Environment"      = "Production"
    "Product"          = "Force and Lock Logs"
    "Owner"            = "CloudSecurity"
    "Team"             = "CloudSecurity"
    "Requester"        = "CloudSecurity"
    "IACRepository"    = "https://github.com/mgcenteno/force-and-lock-logs"
    "Deploy"           = "Terraform"
    "Organization"     = "Own"
  }
}