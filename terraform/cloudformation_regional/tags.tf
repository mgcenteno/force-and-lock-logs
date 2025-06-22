locals {
  common_list = ["Name", "Environment", "BusinessUnit", "Product", "Owner", "Team", "Requester", "Budget", "DisasterRecovery", "EOL", "BusinessImpact", "IACRepository", "Deploy", "Backup", "AutoStartStop", "PatchGroup", "NetworkExposure", "Country", "Organization", "MaintenanceWindow", "TimeZone"]

  tags = {
    for tag in local.common_list : tag => var.tags[tag] if contains(keys(var.tags), tag)
  }
}