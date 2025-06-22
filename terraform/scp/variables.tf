#----------------------#
# Variables a utilizar #
#----------------------#

variable "target_ids" {
  description = "Account, Organizational Unit or Root Account where the Service Control Policies apply and therefore, where the restrictions will apply."
  type        = set(string)
}

variable "scp_name" {
  description = "Service Control Policy name"
  type        = string
}

variable "scp_description" {
  description = "Service Control Policy description"
  type        = string
}

#----------------------#
# Common use variables #
#----------------------#

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