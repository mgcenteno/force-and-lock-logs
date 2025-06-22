{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Deny",
			"Action": [
				"iam:DeleteRole",
				"iam:UpdateRole",
				"iam:UpdateRoleDescription",
				"iam:DetachRolePolicy",
				"iam:PutRolePolicy",
				"iam:UpdateAssumeRolePolicy",
				"iam:AttachRolePolicy",
				"iam:DeleteRolePolicy",
				"iam:PutRolePermissionsBoundary",
				"iam:DeleteRolePermissionsBoundary",
				"iam:CreatePolicyVersion",
				"iam:DeletePolicy",
				"iam:DeletePolicyVersion",
				"iam:SetDefaultPolicyVersion",
				"events:DeleteRule",
				"events:DisableRule",
				"events:PutTargets",
				"events:RemoveTargets",
				"events:PutPermission",
				"events:RemovePermission",
				"events:PutRule",
				"lambda:CreateEventSourceMapping",
				"lambda:DeleteEventSourceMapping",
				"lambda:DeleteFunction",
				"lambda:DeleteFunctionConcurrency",
				"lambda:DeleteFunctionEventInvokeConfig",
				"lambda:PublishLayerVersion",
				"lambda:PublishVersion",
				"lambda:PutFunctionConcurrency",
				"lambda:PutFunctionEventInvokeConfig",
				"lambda:PutProvisionedConcurrencyConfig",
				"lambda:PutRuntimeManagementConfig",
				"lambda:UpdateEventSourceMapping",
				"lambda:UpdateFunctionCode",
				"lambda:UpdateFunctionCodeSigningConfig",
				"lambda:UpdateFunctionConfiguration",
				"lambda:UpdateFunctionEventInvokeConfig",
				"lambda:AddPermission",
				"lambda:RemovePermission",
				"lambda:AddLayerVersionPermission",
				"cloudformation:DeleteGeneratedTemplate",
				"cloudformation:DeleteStack",
				"cloudformation:DeleteStackInstances",
				"cloudformation:DeleteStackSet",
				"cloudformation:DeregisterType",
				"cloudformation:StopStackSetOperation",
				"cloudformation:UpdateGeneratedTemplate",
				"cloudformation:UpdateStack",
				"cloudformation:UpdateStackInstances",
				"cloudformation:UpdateStackSet",
				"cloudformation:UpdateTerminationProtection",
				"cloudformation:SetStackPolicy"
			],
			"Resource": [
				"arn:aws:iam::*:role/iamrole-fall-enable-cloudfront-access-logs",
				"arn:aws:iam::*:role/iamrole-fall-enable-elb-access-logs",
				"arn:aws:iam::*:role/iamrole-fall-enable-s3-access-logging",
				"arn:aws:iam::*:role/iamrole-fall-enable-vpc-flow-logs",
				"arn:aws:iam::*:role/iamrole-fall-publish-vpc-flow-logs",
				"arn:aws:iam::*:policy/iamplcy-fall-enable-cloudfront-standard-logs",
				"arn:aws:iam::*:policy/iamplcy-fall-enable-elb-access-logs",
				"arn:aws:iam::*:policy/iamplcy-fall-enable-s3-access-logging",
				"arn:aws:iam::*:policy/iamplcy-fall-enable-vpc-flow-logs",
				"arn:aws:events:*:*:rule/eventrule-fall-new-cloudfront-distribution-created",
				"arn:aws:events:*:*:rule/eventrule-fall-new-elb-created",
				"arn:aws:events:*:*:rule/eventrule-fall-new-s3-bucket-created",
				"arn:aws:events:*:*:rule/eventrule-fall-new-vpc-created",
				"arn:aws:lambda:*:*:function:lambfun-fall-enable-s3-access-logging*",
				"arn:aws:lambda:*:*:function:lambfun-fall-enable-cloudfront-access-logs*",
				"arn:aws:lambda:*:*:function:lambfun-fall-enable-elb-access-logs*",
				"arn:aws:lambda:*:*:function:lambfun-fall-enable-vpc-flow-logs*",
				"arn:aws:cloudformation:*:*:stack/StackSet-StacksetForceAndLockLogs-*"
			],
			"Condition": {
				"StringEquals": {
					"aws:PrincipalOrgID": "${org_id}"
				},
				"ArnNotLike": {
					"aws:PrincipalArn": "arn:aws:iam::*:role/stacksets-exec-*"
				},
				"ForAllValues:StringEquals": {
					"aws:CalledVia": "cloudformation.amazonaws.com"
				}
			}
		},
		{
			"Effect": "Deny",
			"Action": [
				"logs:DeleteLogGroup",
				"logs:DeleteLogStream",
				"logs:DeleteRetentionPolicy",
				"logs:DisassociateKmsKey",
				"logs:DeleteSubscriptionFilter",
				"logs:PutRetentionPolicy",
				"logs:PutSubscriptionFilter",
				"logs:DeleteResourcePolicy",
				"logs:PutResourcePolicy",
				"s3:DeleteBucket",
				"s3:DeleteObject",
				"s3:DeleteObjectVersion",
				"s3:InitiateReplication",
				"s3:PutEncryptionConfiguration",
				"s3:PutLifecycleConfiguration",
				"s3:PutReplicationConfiguration",
				"s3:PutObjectRetention",
				"s3:DeleteBucketPolicy",
				"s3:ObjectOwnerOverrideToBucketOwner",
				"s3:PutBucketPolicy",
				"s3:PutBucketAcl",
				"s3:PutBucketOwnershipControls",
				"s3:PutBucketPublicAccessBlock",
				"s3:PutObjectAcl",
				"s3:PutObjectVersionAcl",
				"s3:PutBucketVersioning"
			],
			"Resource": [
				"arn:aws:logs:*:*:log-group:/vpc-flow-logs*",
				"arn:aws:s3:::s3bkt-access-logging-*"
			],
			"Condition": {
				"StringEquals": {
					"aws:PrincipalOrgID": "${org_id}"
				},
				"ArnNotLike": {
					"aws:PrincipalArn": [
						"arn:aws:iam::*:role/iamrole-fall-enable-cloudfront-access-logs",
						"arn:aws:iam::*:role/iamrole-fall-enable-elb-access-logs",
						"arn:aws:iam::*:role/iamrole-fall-enable-s3-access-logging",
						"arn:aws:iam::*:role/iamrole-fall-enable-vpc-flow-logs",
						"arn:aws:iam::*:role/iamrole-fall-publish-vpc-flow-logs"
					]
				},
				"ForAllValues:StringEquals": {
					"aws:CalledVia": "lambda.amazonaws.com"
				}
			}
		},
		{
			"Effect": "Deny",
			"Action": [
				"ec2:DeleteFlowLogs",
				"cloudfront:DeleteRealtimeLogConfig"
			],
			"Resource": [
				"*"
			]
		}
	]
}