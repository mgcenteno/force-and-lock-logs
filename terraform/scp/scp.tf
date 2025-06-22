#------------------------------------#
# Se crea una Service Control Policy #
#------------------------------------#


resource "aws_organizations_policy" "scp_policy_fall" {
  name        = var.scp_name
  description = var.scp_description

  content = templatefile("${path.module}/../../policies/scp-protect-fall-resources.tpl", {
  org_id = data.aws_organizations_organization.organization.id
})


  tags = var.tags
}

#---------------------------------#
# Se asocia la SCP con la OU Root #
#---------------------------------#

resource "aws_organizations_policy_attachment" "scp_policy_fall_attachment" {
  for_each  = var.target_ids
  policy_id = aws_organizations_policy.scp_policy_fall.id
  target_id = each.value
}