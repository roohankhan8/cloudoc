# CloudDoc Project Plan

## Goal

Build a Django REST API that accepts PDF, CSV, and Excel documents, stores them in S3, processes them asynchronously, and exposes status and extracted data. Use Floci for local AWS learning first, then validate selected behavior in AWS.

## Project boundaries

- PostgreSQL is a normal local database service; Floci emulates AWS services.
- Begin with the Floci and AWS CLI S3 exercise. Do not start Django APIs until that checkpoint passes.
- Add only the service abstraction needed to switch local and AWS endpoints cleanly.
- Treat real AWS deployment as the final, cost-conscious milestone. Set billing alerts and use least-privilege IAM.

## Milestones

**Progress:** Milestone 1 completed. Milestone 2 implementation is in progress.

### 1. Local cloud foundation

**Learn:** cloud regions, AWS CLI and SDK basics, emulator boundaries.

**Build:** Install Docker Desktop, Floci CLI, and AWS CLI; run Floci; create an S3 bucket; upload/download a file; list buckets with Boto3.

**Done when:** CLI and Boto3 both reach the Floci endpoint with dummy credentials, and the uploaded object can be retrieved. Record the commands and any setup issue.

### 2. Django API and S3 storage

**Learn:** Django/DRF API structure, S3 buckets/objects, metadata, validation, presigned URLs.

**Build:** Scaffold the Django project, PostgreSQL, and a documents app. Add validated document upload, metadata persistence, download URL, and deletion. Keep object storage configuration endpoint-based so Floci and AWS can be selected through environment settings.

**Done when:** API requests can upload, inspect, download, and delete a document locally; invalid type and oversized-file cases are rejected; database metadata and object state agree.

### 3. Queue and background worker

**Learn:** SQS standard queues, visibility timeout, retention, long polling, at-least-once delivery, idempotency, and dead-letter queues.

**Build:** Publish a processing message after upload; add a Python worker that receives messages and updates document status; add retry/failure handling and a dead-letter queue.

**Done when:** Processing happens outside the request, duplicate delivery does not duplicate results, and a permanently failing message can be inspected and retried deliberately.

### 4. Document extraction and Lambda

**Learn:** Lambda execution model, triggers, roles, cold starts, timeouts, and retry behavior.

**Build:** Extract a small, defined set of invoice fields from a sample PDF. Compare a local worker path with an SQS-triggered Lambda path where supported by Floci.

**Done when:** A sample document produces persisted extracted data and failures are visible. Document which behaviors require confirmation in real AWS.

### 5. Security and permissions

**Learn:** least privilege, IAM users/roles/policies, temporary credentials, secrets, and basic VPC concepts.

**Build:** Remove credentials from source/config files, use environment configuration and local dummy credentials, enforce document ownership/authorization, and define narrowly scoped AWS permissions for deployment.

**Done when:** Unauthorized document access is denied, secrets are absent from the repository, and the permissions needed by each component are documented.

### 6. Monitoring and operations

**Learn:** structured logs, CloudWatch logs/metrics/alarms, health checks, and tracing concepts.

**Build:** Log document and message identifiers, track processing outcomes/duration and queue depth, and add health checks. Add a basic dashboard/alarm only where supported and useful.

**Done when:** A failed document can be followed from API request through worker logs, and basic processing health is measurable.

### 7. Infrastructure and CI/CD

**Learn:** Terraform state/providers, infrastructure as code, CI workflows, image build and deployment.

**Build:** Define repeatable AWS resources in Terraform; add GitHub Actions for code checks and integration against Floci; build a Docker image and document deployment steps.

**Done when:** A clean checkout can run the documented checks, and infrastructure changes are reviewable before apply. Do not commit Terraform state or secrets.

### 8. AWS validation and production readiness

**Learn:** VPC/networking, RDS, ECS or EC2, load balancing, cost controls, availability, and recovery.

**Build:** Set billing alerts first. Deploy a small environment, configure real S3/SQS and IAM roles, run the API and worker, and compare behavior to Floci. Tear down resources that are not needed.

**Done when:** The deployed flow completes an upload and processing cycle, monitoring is usable, setup/teardown is documented, and Floci differences are recorded.

## Suggested repository shape

Create this structure incrementally as the milestones need it; do not create empty future folders up front.

```text
backend/                 Django project and apps
  config/
  apps/documents/
  apps/processing/
  services/storage/
  services/messaging/
workers/                  Local worker and Lambda entry point
infrastructure/           Local Compose and Terraform when needed
docs/                     Architecture, learning notes, deployment notes
.github/workflows/        CI when milestone 7 begins
```

## Learning loop for each service

1. State the problem the service solves and identify its core concepts.
2. Experiment with AWS CLI against Floci before adding application code.
3. Integrate one feature into CloudDoc and document the decision.
4. Exercise failure cases, retries, permissions, and duplicate events.
5. Record what Floci does not emulate and verify those points against AWS only when needed.

## Completion checklist

- [ ] S3 document storage and metadata API works.
- [ ] SQS-driven processing is asynchronous and idempotent.
- [ ] Lambda flow and its emulator limitations are documented.
- [ ] Access control and least-privilege permissions are in place.
- [ ] Logs and basic processing metrics help diagnose failures.
- [ ] CI and Terraform provide repeatable checks and infrastructure.
- [ ] A small AWS deployment has been validated, monitored, and safely torn down or cost-controlled.
- [ ] Architecture, setup, and AWS-versus-Floci differences are documented.
