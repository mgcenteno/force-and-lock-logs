# Force and Lock Logs (FALL)

Force and Lock Logs is a tool created by the Mariano Gabriel Centeno that arises as an initiative to satisfy a specific need that became relevant due to different security incidents, the objective is to make available many log sources under a scheme in which it does not depend exclusively on whether developers, devops, or anyone who deploys infrastructure and workloads in the cloud, remember to enable the logging features of each service (See Scope Section).

To achieve our goal we use combination of Infrastructure as Code is used, (Terraform and AWS CloudFormation), to deploy a series of services in an Event-Driven Architecture scheme, which will be responsible, on the one hand, for enabling logging in the services (In case they are not active) and on the other hand, to prevent them from being modified and / or altered in any way, restricting these potentially dangerous actions through service control policies (SCP) at a hierarchical level and taking precedence, thus preventing even privileged users from being able to exceed this barrier.

The rest of this folder contains various architecture and flow diagrams that explain in more detail how Force and Lock Logs (FALL) can help us achieve this goal.

# Architecture Diagram
Below is the solution architecture diagram, showing how the various services and resources are connected to achieve the goal of obtaining logs and, in turn, protecting them from malicious actions that could hinder an investigation or even troubleshooting.

![Architecture Diagram Force and Lock Logs](./images/Force_and_Lock_Logs_AWS.png)

# Scope:

At the time of writing, Force and Lock Logs covers the following resources/services:

* VPC Flow Logs

* ELB Access Logs (Application and Network)

* CloudFront Distribution Standard Logs v2

* Amazon S3 Access Logs


# How do we deploy "Force and Lock Logs"?

The deployment phase consists of a series of steps that are explained below:

![GitHub repository structure.](./images/Force_and_Lock_Logs_Deployment.png)

Infrastructure as Code and automation, the heart of FALL:

For the deployment of this tool, a combination of Terraform and AWS CloudFormation is used, and it's recommmended use in conjunction with GitHub Actions using an OIDC with temporary AWS credentials, although on the other hand it does not offer us the level of flexibility that AWS CloudFormation has to automate the deployment in all the accounts of the organization and with the possibility of an Automatic deployment in new accounts, hence this hybrid deployment.

To be able to deploy FALL, you need to clone and upload this code in your own private repository and configure one pipeline "deploy.yaml", which allows you to assume an IAM Role in the root account of an AWS organization or delegated AWS account, this in turn is authenticated through a custom Identity Provider using Open ID Connect (OIDC) which allows GitHub to assume temporary credentials by making an AssumeRoleWithWebIdentity type API call with a trust policy limited to the repository where the Force and Lock Logs code is stored.

After these steps, Terraform deploys a series of AWS resources, the main one being an AWS CloudFormation StackSet, with the Automatic Deployment feature, which has the necessary definitions to deploy the resources and/or configurations of relevant services both to force logging of the required services such as Elastic Load Balancers or VPC Flow Logs, and to then block their possible modification or deletion through Service Control Policies (SCPs).

 

Having this in mind, we can continue learning what happen in each AWS account within our environment:

# Management Account:
The organization's root account will act as the primary resource for generating SCPs to ensure that the logs captured by AWS cannot be altered by any principal of each member account, except for a limited list of privileged users within the management account.
Only the SCPs are deployed in this account, and administration of the AWS CloudFormation service is delegated to another account. This allows approach allow us to deploy our tool to the entire AWS Organization and, consequently, all existing and future accounts. This avoids having to perform new executions each time a new account is created.


# Delegated Administrator Account:
The account designated as the administrator of the AWS CloudFormation service generates a StackSet, which can deploy a Stack. In short, it is a template written in YAML or JSON that defines the services and resources to be deployed in an AWS account. However, using what is called a StackSet, deployment can be done to multiple accounts and/or multiple regions at the same time, as well as to new accounts created after the StackSet itself is created, making it highly scalable. Here, the CloudFormation template used is one written in .yaml and stored in the same GitHub repository where the Terraform code is defined. It is located at: force-and-lock-logs/templates/stackset_Force_and_Lock_Logs_instance.yaml

 
# Member Accounts:
In member accounts, through IaC, we deploy an Event-driven architecture that includes the following services and/or resources:

Amazon EventBridge Rules, which allow us to capture certain events within the AWS environment, for example, a CreateVPC, and then send the event to a destination, which in this case would be a Lambda function.

AWS Lambda functions allow us to execute Python code that activates the Logging features of each of the other services and/or resources based on events detected by Amazon EventBridge.

In some of these cases, it is necessary to grant permissions to different services so they can execute the necessary actions. We achieve this through the use of IAM Roles, which they can use for this delegation. In turn, to follow the principle of least privilege within our tool, we use IAM Policies, with the minimum necessary permissions for each task. In addition, we securely configure a trust policy so that only authorized services, under the defined conditions, can assume the created roles.

To maintain the security of logs at rest, as well as temporary storage for other services, encryption keys are used. These keys are created and managed by the AWS KMS (Key Management Service). Key Policies are applied to them. These are a special type of resource-based policy that allows you to limit the actions that can be performed with that key and define who can use it, including under what conditions. This is also based on the principle of least privilege.

The tool also allows for sending notifications messages through Webhook that can be Google Chat, Slack or Microsoft Teams. Notifications indicate application status changes to logging configurations, as well as attempts to modify those attributes.

 

# Example:

Below is an example of how Lock and Force would act in the following scenario:
A new VPC is created. This event (CreateVpc) is captured by the Amazon EventBridge service, and through an Event Rule, it takes that event and passes it to a destination or target, in this case a Lambda function, which has an IAM Role with the necessary permissions to execute a series of actions using boto3 in Python. This role is responsible for enabling the VPC Flow Logs feature of the newly created VPC, which associates it with an IAM Role with permissions to save those logs in a CloudWatch Log Group encrypted at rest by a cryptographic key created in AWS KMS. A notification is then sent via the configured Webhook.

 

# Post-Deployment:


Once Lock and Force is deployed, scenarios may arise such as:
Someone attempting to delete logs from a CloudWatch Log Group or modify their retention, modify the permissions of the IAM Role used by a VPC Flow Logs, etc. In this case, a Service Control Policy would come into play to prevent these changes, for example, "DeleteFlowLogs" with a statement like the following:

![Statement](./images/DeleteFlowLogs_example.png)




# Pending

* Modify CloudFormation, Terraform and Deploy.yaml to allow Multi-Region deployments
* Update Workflow diagrams
* Update Deployment Diagram
* Update Infrastructure Diagram
* Update README.md to explain why FALL?
* Add CloudTrail Data Plane Events as an recommendation and why each one in S3 Server Access Logs
* Test GitHub Repo Public Access, just to clone, Deny anything else.
* Create a FALL Logo.




------

✅ Resumen comparativo
Característica	CloudTrail Data Events para S3	S3 Server Access Logs
Nivel de detalle	Muy detallado: operaciones de objetos (GetObject, PutObject, etc.)	Más básico: requests HTTP al bucket
Qué registra	Eventos a nivel de API sobre objetos (lecturas, escrituras)	Accesos al bucket vía HTTP (quién accedió, cuándo, desde dónde)
Formato	JSON estructurado (útil para análisis y SIEM)	Texto en formato de log estilo Apache
Tiempo de entrega	Cerca del tiempo real (pocos minutos)	Puede demorar varias horas
Costo	Se cobra por evento registrado	Gratis (excepto el almacenamiento en S3)
Soporta CloudWatch Logs/Insights	Sí	No directamente
Casos de uso	Auditoría fina, detección de amenazas, cumplimiento	Estadísticas de uso, diagnóstico de accesos

🧠 Explicación más detallada
📘 1. CloudTrail Data Events para S3
No están habilitados por defecto.

Se activan por bucket o por prefijo dentro del bucket.

Registran operaciones a nivel de objeto: GetObject, PutObject, DeleteObject, ListBucket, etc.

Incluyen información como:

Usuario/rol que ejecutó la acción

Hora y región

IP de origen

Resultado (éxito/error)

ARN del recurso afectado

Casos de uso clave:

Cumplimiento normativo (p. ej., ver quién accedió a datos sensibles)

Análisis forense

Integración con Amazon GuardDuty, SIEMs y CloudWatch

📗 2. S3 Server Access Logs
Se habilitan a nivel de bucket.

Cada vez que alguien hace un request HTTP (p. ej., GET /object.jpg), se genera un log en formato texto.

Incluye:

IP del solicitante

Tiempo del request

Acción HTTP (GET, PUT, etc.)

Código de respuesta

Bytes transferidos

Agente de usuario

Casos de uso clave:

Estadísticas de tráfico

Detección de patrones de uso anómalos (pero más limitada)

Costos y optimización

🧪 ¿Cuál elegir?
Depende de tus objetivos:

Objetivo	Opción recomendada
Auditoría detallada por cumplimiento	✅ CloudTrail Data Events
Estadísticas generales de acceso	✅ S3 Server Access Logs
Detección de uso malicioso o no autorizado	✅ CloudTrail Data Events
Minimizar costos	❗ Server Access Logs (pero cuidado: poco detalle)