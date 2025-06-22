locals {
  common_list = ["Name", "Environment", "Product", "Owner", "Team", "Requester", "IACRepository", "Deploy", "Organization"]

  tags = {
    for tag in local.common_list : tag => var.tags[tag] if contains(keys(var.tags), tag)
  }
}

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