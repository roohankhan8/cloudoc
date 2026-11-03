# CloudDoc: AWS + Floci Project Roadmap

## Project overview

Build a **Cloud-Native Document Processing Platform** using Django, AWS services, Docker, and Floci.

The objective is to learn how real backend systems use AWS infrastructure, how developers deploy applications, and how DevOps engineers automate infrastructure.

By the end, the application will use object storage, queues, serverless functions, databases, monitoring, IAM, and CI/CD.

## 1. What are we building?

### CloudDoc — Document Processing Platform

A platform where users upload documents (PDF, CSV, Excel), and the system processes them asynchronously using cloud infrastructure.

### Example user journey

1. A user uploads a PDF invoice through the Django REST API.
2. The backend stores the file in AWS S3.
3. The backend sends a processing message to AWS SQS.
4. A background worker receives the message.
5. The worker extracts information from the PDF.
6. Extracted information is saved in PostgreSQL.
7. The user retrieves the processing status and extracted data through an API.
8. The system records logs, failures, and processing metrics.

## 2. Architecture

We will build the system incrementally. Initially, everything will run locally through Floci. Later, we will replace local cloud endpoints with actual AWS services.

```text
                  USER
                   |
                   v
             Django REST API
                   |
          +--------+--------+
          |                 |
          v                 v
      PostgreSQL         Floci S3
      (Metadata)         (Documents)
                            |
                            v
                         Floci SQS
                            |
                            v
                     Background Worker
                            |
                            v
                    Document Extraction
                            |
                            v
                       PostgreSQL
                            |
                            v
                       REST API
                            |
                            v
                          USER
```

## 3. Technology stack

| Technology | Purpose | What you will learn |
|---|---|---|
| Python | Primary language | Backend development |
| Django + DRF | REST API | API architecture |
| PostgreSQL | Application database | SQL, transactions, indexing |
| Docker | Containerization | Containers and networking |
| Floci | Local cloud environment | Cloud emulation |
| AWS S3 | File storage | Object storage |
| AWS SQS | Message processing | Event-driven architecture |
| AWS Lambda | Serverless processing | Serverless computing |
| AWS IAM | Permissions | Cloud security |
| AWS CloudWatch | Monitoring | Logs and metrics |
| GitHub Actions | CI/CD | Automated deployment |
| Terraform | Infrastructure | Infrastructure as Code |

**Important distinction:** PostgreSQL will initially run as a normal Docker service. Floci will emulate the cloud services. We will use actual AWS later to understand the differences between local emulation and production infrastructure.

## 4. Learning roadmap — 8 weeks

### Phase 1 — Foundation and local infrastructure

**Timeline:** Week 1

**Goal:** Understand cloud computing and run your first local cloud environment.

**AWS concepts**
- What is cloud computing?
- IaaS, PaaS and SaaS.
- AWS regions and availability zones.
- AWS global infrastructure.
- AWS CLI and SDKs.
- Cloud service models.

**Implementation**
- Install Docker Desktop.
- Install Floci CLI.
- Start the AWS emulator.
- Configure AWS CLI to communicate with Floci.
- Create your first S3 bucket.
- Upload and download files.

**Deliverable:** Working local AWS environment with S3.

### Phase 2 — Storage and object management

**Timeline:** Week 2

**Goal:** Learn AWS S3 and integrate it into Django.

**AWS concepts**
- S3 buckets and objects.
- Object keys and metadata.
- Bucket policies.
- Access control.
- Presigned URLs.
- Lifecycle policies and versioning.

**Implementation**
- Create document upload API.
- Upload documents to Floci S3.
- Save file metadata in PostgreSQL.
- Generate presigned download URLs.
- Implement document deletion.
- Validate file types and file sizes.

**Deliverable:** Fully functional document storage API.

### Phase 3 — Messaging and asynchronous processing

**Timeline:** Week 3

**Goal:** Understand event-driven architecture.

**AWS concepts**
- SQS queues.
- Standard vs FIFO queues.
- Visibility timeout.
- Message retention.
- Dead-letter queues.
- Long polling.
- At-least-once delivery and idempotency.

**Implementation**
- Create an SQS queue.
- Send a message whenever a document is uploaded.
- Build a Python background worker.
- Consume messages from SQS.
- Process documents asynchronously.
- Implement retries and failed-message handling.

**Deliverable:** Asynchronous document processing pipeline.

### Phase 4 — Serverless computing

**Timeline:** Week 4

**Goal:** Understand AWS Lambda and serverless architecture.

**AWS concepts**
- What is serverless computing?
- Lambda functions.
- Lambda execution roles.
- Event triggers.
- Cold starts.
- Execution limits.
- Lambda and SQS integration.

**Implementation**
- Write a Python Lambda function.
- Trigger processing through SQS.
- Extract PDF invoice information.
- Store extracted results in PostgreSQL.
- Handle Lambda failures and retries.

**Deliverable:** A serverless document-processing workflow.

**Note:** Floci's Lambda emulation should be used for local experimentation; validate the actual deployment and execution model in AWS.

### Phase 5 — Security and permissions

**Timeline:** Week 5

**Goal:** Understand how AWS secures infrastructure.

**AWS concepts**
- IAM users and roles.
- IAM policies.
- Least privilege principle.
- AWS access keys.
- Temporary credentials.
- Secrets Manager.
- Security groups and VPC fundamentals.

**Implementation**
- Create appropriate IAM roles and policies.
- Remove hardcoded credentials.
- Configure environment variables.
- Secure document access.
- Implement permission checks.
- Audit access and secrets handling.

**Deliverable:** Secure cloud application architecture.

### Phase 6 — Monitoring and observability

**Timeline:** Week 6

**Goal:** Learn how production applications are monitored.

**AWS concepts**
- CloudWatch logs.
- CloudWatch metrics.
- CloudWatch alarms.
- Distributed tracing.
- Error monitoring.
- Application health checks.

**Implementation**
- Add structured application logs.
- Monitor processing failures.
- Track processing duration.
- Record queue depth.
- Configure alarms.
- Build an operational dashboard.

**Deliverable:** Observable backend system.

### Phase 7 — Infrastructure as Code and CI/CD

**Timeline:** Week 7

**Goal:** Learn how infrastructure and application deployments are automated.

**AWS concepts**
- Terraform fundamentals.
- Infrastructure as Code.
- Terraform providers and state.
- GitHub Actions.
- CI/CD pipelines.
- Docker image deployment.

**Implementation**
- Write Terraform configurations for AWS resources.
- Create reusable infrastructure modules.
- Configure GitHub Actions.
- Run automated tests against Floci in CI.
- Build and publish Docker images.
- Automate AWS deployment.

**Deliverable:** Automated infrastructure and deployment pipeline.

### Phase 8 — Real AWS deployment and production readiness

**Timeline:** Week 8

**Goal:** Move from local cloud emulation to real AWS.

**AWS concepts**
- Production architecture.
- AWS networking and VPC.
- RDS.
- ECS or EC2.
- Application Load Balancer.
- Cost management.
- High availability and disaster recovery.

**Implementation**
- Create an AWS account and configure billing alerts.
- Deploy the Django application.
- Create real S3 and SQS resources.
- Deploy processing workers.
- Configure IAM roles.
- Configure CloudWatch.
- Test the deployed application.
- Document architecture and deployment.

**Deliverable:** A deployed cloud-native application.

## 5. Project repository structure

Maintain a modular repository rather than putting everything into one Django project folder.

```text
clouddoc/
│
├── backend/
│   ├── config/
│   ├── apps/
│   │   ├── users/
│   │   ├── documents/
│   │   └── processing/
│   │
│   ├── services/
│   │   ├── storage/
│   │   ├── messaging/
│   │   └── extraction/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── workers/
│   ├── document_worker/
│   └── lambda/
│
├── infrastructure/
│   ├── local/
│   │   └── docker-compose.yml
│   └── terraform/
│       ├── modules/
│       └── environments/
│
├── scripts/
│
├── .github/
│   └── workflows/
│
├── docs/
│   ├── architecture.md
│   ├── aws-learning-notes.md
│   └── deployment.md
│
├── .env.example
├── .gitignore
└── README.md
```

### Important architectural decision: cloud service abstraction

Create interfaces for cloud services so the application does not need to know whether it is communicating with local Floci or actual AWS.

For example:

```python
class StorageService:

    def upload(self, file, key):
        raise NotImplementedError

    def download(self, key):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError
```

Then implement:

```text
StorageService
     |
     +---- FlociS3Storage
     |
     +---- AWSS3Storage
```

This is an example of dependency inversion and abstraction. It makes testing and switching infrastructure significantly easier.

## 6. How to learn each AWS service

For every AWS service, follow this learning cycle:

1. **Understand the problem:** What problem does this AWS service solve? Why does it exist?
2. **Understand the architecture:** Learn its components, limitations, terminology, and interactions with other services.
3. **Experiment using Floci:** Create resources, configure them, and interact with them using AWS CLI and Python SDKs.
4. **Integrate into CloudDoc:** Implement a real feature using the service.
5. **Break things intentionally:** Test permission errors, network failures, retries, duplicate messages, and resource failures.
6. **Validate against AWS:** Deploy a small version to actual AWS and understand the differences.

## 7. Progress and completion criteria

By the end, demonstrate these capabilities:

| Skill | Expected outcome |
|---|---|
| AWS S3 | Upload, retrieve and manage files |
| AWS SQS | Build asynchronous processing |
| AWS Lambda | Develop serverless functions |
| AWS IAM | Design least-privilege permissions |
| AWS CloudWatch | Monitor application behavior |
| AWS CLI | Manage cloud resources |
| Boto3 | Interact with AWS through Python |
| Docker | Containerize the application |
| Terraform | Provision infrastructure |
| GitHub Actions | Automate testing and deployment |
| AWS deployment | Run the application in production |

You should also be able to explain why you chose each service and what alternatives exist.

## 8. Important project rules

1. Don't skip AWS fundamentals just because Floci makes things easier.
2. Use AWS CLI before relying entirely on Python SDKs.
3. Understand what each AWS service does before integrating it.
4. Don't hardcode AWS credentials anywhere.
5. Write tests for failures, not just successful requests.
6. Document architectural decisions in `docs/`.
7. Keep local development and production configurations separate.
8. Don't deploy expensive infrastructure just to demonstrate a concept.

**Important limitation:** Floci is an emulator, not a complete AWS replacement. Some AWS-specific behavior, IAM permissions, networking, quotas, and service integrations need to be tested against actual AWS.

## 9. Week 1 checklist

Your first milestone is to establish the development environment.

Use PowerShell on Windows.

- [ ] Install Docker Desktop and verify Docker works.
- [ ] Install Floci CLI for Windows.
- [ ] Start the Floci AWS emulator.
- [ ] Install and configure AWS CLI.
- [ ] Configure local AWS credentials (dummy credentials).
- [ ] Create an S3 bucket using AWS CLI.
- [ ] Upload and download a file.
- [ ] Write a Python script using Boto3 to list S3 buckets.
- [ ] Document the architecture and commands.

**Progress tracking:** Mark each item complete only after you have run it and verified the result.

## 10. How we will work through the project

Treat this as an engineering project, not just a course.

For each milestone:
- Learn the underlying concepts before using the service.
- Implement the feature in CloudDoc.
- Run and inspect the relevant tests.
- Investigate failures rather than copying fixes blindly.
- Review the code and architecture.
- Record what you learned and what remains unclear.
- Move to the next milestone only when the current one works.

### First objective

Get Docker, Floci, and AWS CLI running on your Windows machine.

**Do not start building Django APIs yet.** Understanding the local cloud environment comes first.
