locals {
  common_list = ["Name", "Environment", "Product", "Owner", "Team", "Requester", "IACRepository", "Deploy", "Organization"]

  tags = {
    for tag in local.common_list : tag => var.tags[tag] if contains(keys(var.tags), tag)
  }
}