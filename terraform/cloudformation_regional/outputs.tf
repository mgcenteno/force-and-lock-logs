output "global_stack_name_primary" {
  value = aws_cloudformation_stack.regional_resources_fall_root_org_primary.name
}

output "global_stack_name_secondary" {
  value = aws_cloudformation_stack.regional_resources_fall_root_org_secondary.name
}