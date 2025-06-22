#--------------------------------------#
# Se capturan los datos del account ID #
#--------------------------------------#

data "aws_caller_identity" "current" {}

data "aws_organizations_organization" "organization" {}