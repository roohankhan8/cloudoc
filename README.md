# CloudDoc

CloudDoc is a Django learning project for uploading invoices, extracting a few fields, and processing them asynchronously with PostgreSQL and AWS services. Milestones 1-7 cover local Floci setup, the Django document interface/API, SQS, Lambda extraction, access control, monitoring, and repeatable infrastructure/CI.

See [the project plan](docs/PROJECT_PLAN.md) and [the original roadmap](CloudDoc_AWS_Floci_Project_Roadmap.md).

## Requirements

- Windows with PowerShell
- Python 3.12+
- Docker Desktop running Linux containers
- Floci CLI, AWS CLI v2

## Start the local services

From the project folder, create a local environment file if you do not already have one, then start Floci:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
floci start
floci doctor
```

The example config uses the `my-floci-bucket` bucket from the Milestone 1 scripts. Create it if it does not exist:

```powershell
aws --endpoint-url http://localhost:4566 s3 mb s3://my-floci-bucket
```

Start PostgreSQL in Docker:

```powershell
docker compose up -d postgres
docker compose ps
```

The Django server runs on your Windows host and connects to PostgreSQL on `127.0.0.1:5434` and Floci on `localhost:4566`.

## Install and run Django

Activate the existing virtual environment, or create one if needed:

```powershell
if (-not (Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create the database tables and SQS queues:

```powershell
python manage.py migrate
python manage.py setup_sqs
```

Create a login for the document workspace and API:

```powershell
python manage.py createsuperuser
```

Sign in at `http://127.0.0.1:8000/accounts/login/`. Each account can access only its own documents. Existing documents created before ownership was added remain in storage and require an administrator to assign an owner before they appear to a user.

Start the API in one PowerShell window:

```powershell
python manage.py runserver
```

Start the worker in a second window with the virtual environment activated:

```powershell
python manage.py process_documents
```

The frontend is available at `http://127.0.0.1:8000/`; the API remains available at `http://127.0.0.1:8000/api/documents/`.

## Docker image

Build the API and worker image:

```powershell
docker build -t clouddoc:local .
```

Run migrations, then start the API. From a container, use `host.docker.internal` to reach PostgreSQL and Floci on the Windows host:

```powershell
docker run --rm --env-file .env -e DB_HOST=host.docker.internal -e DB_PORT=5434 -e AWS_ENDPOINT_URL=http://host.docker.internal:4566 clouddoc:local python manage.py migrate --noinput
docker run --rm --env-file .env -e DB_HOST=host.docker.internal -e DB_PORT=5434 -e AWS_ENDPOINT_URL=http://host.docker.internal:4566 -p 8000:8000 clouddoc:local
```

Run the worker in another container from the same image:

```powershell
docker run --rm --env-file .env -e DB_HOST=host.docker.internal -e DB_PORT=5434 -e AWS_ENDPOINT_URL=http://host.docker.internal:4566 --entrypoint python clouddoc:local manage.py process_documents
```

Set `AWS_ENDPOINT_URL` to an empty value and use an IAM role when running against AWS. Configure `ALLOWED_HOSTS`, a private `SECRET_KEY`, and HTTPS ingress for any network deployment.

## Terraform and CI

GitHub Actions runs Django checks and migrations against PostgreSQL, exercises the upload-to-S3/SQS path against Floci, validates Terraform, and builds the Docker image on pushes and pull requests.

The Terraform files in `infrastructure/terraform` define an encrypted, private document bucket, processing and dead-letter queues, separate least-privilege API and processor policies, and a Lambda execution role. Configure AWS credentials through the CLI or an IAM role (not `.tfvars`), then initialize, review, and plan before applying:

```powershell
cd infrastructure/terraform
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan -var="document_bucket_name=your-globally-unique-bucket-name"
```

After reviewing the plan, run `terraform apply` with the same variable. Terraform uses local state by default; `terraform.tfstate`, `.tfvars`, and plan files are ignored. Do not commit state or credentials. Attach the API policy to the API role and use the output `processor_role_arn` as the Lambda execution role. This milestone does not create networking, a database, or the application runtime in AWS.

## Health and processing logs

`GET http://127.0.0.1:8000/health/` checks PostgreSQL and the processing queue. It returns HTTP 200 when both respond, otherwise 503; the JSON includes approximate visible queue depth and in-flight message count. Poll it from an internal uptime checker to record queue and service health. Keep this endpoint behind trusted ingress because it is unauthenticated and exposes operational counts. The API role needs `sqs:GetQueueUrl` and `sqs:GetQueueAttributes` for this check.

Django writes JSON logs to the console. Upload and queue events share a document ID; worker events include the SQS message ID, receive attempt, outcome, and processing duration. Invoice field values are not written to logs. In CloudWatch Logs Insights, use:

```text
fields @timestamp, event, document_id, message_id, attempts, outcome, duration_ms, queue_depth
| filter event in ["document_processing", "document_queued", "health_check"]
| sort @timestamp desc
```

Create CloudWatch metric filters or alarms for repeated `outcome = "failed"` processing events and sustained queue depth if needed; this project does not provision a dashboard or alarm.

## Invoice extraction

The worker extracts `invoice_number`, `invoice_date`, and `total_amount` from text-based PDFs and saves them in PostgreSQL. Results appear in the frontend and document API response. Use labels such as `Invoice Number: INV-1001`, `Invoice Date: 2026-01-15`, and `Total: USD 125.00`. Image-only scans need OCR, which this milestone does not include. CSV and XLSX uploads are still accepted, but extraction currently supports PDFs only.

Sample invoices for testing are in [`output/pdf/`](output/pdf/):

- [USD invoice](output/pdf/sample-invoice-usd.pdf): `INV-2026-001`, `2026-11-04`, `USD 1,249.50`
- [PKR invoice](output/pdf/sample-invoice-pkr.pdf): `INV-2026-002`, `2026-10-28`, `PKR 48,750.00`
- [Minimal invoice](output/pdf/sample-invoice-minimal.pdf): `INV-2026-003`, `2026-09-15`, `USD 89.99`

## Run the same processor through Lambda

Stop the local `process_documents` worker first so it does not consume messages alongside Lambda. Then run one script to package the function, create or update it, and connect the processing queue:

```powershell
.\scripts\package_lambda.ps1
```

The script reads database, AWS, bucket, and queue settings from `.env` (falling back to `.env.example`). It changes loopback database and Floci endpoints to `host.docker.internal` so the Lambda container can reach services on the Windows host. The default local IAM role ARN is `arn:aws:iam::000000000000:role/lambda-role`; set `LAMBDA_ROLE_ARN` in `.env` or pass `-LambdaRoleArn` if your Floci setup uses a different role. Pass `-LambdaAwsEndpoint` if Lambda needs a custom Floci endpoint.

Upload a PDF from the frontend and watch its status/results update. To return to local-worker mode, remove the Lambda event source mapping before restarting `python manage.py process_documents`. Use `aws lambda list-event-source-mappings` to find its UUID, then `aws lambda delete-event-source-mapping --uuid <uuid>` to remove it.

This demonstrates local event-mapping behavior described in the [Floci Lambda guide](https://floci.io/floci/services/lambda/). Lambda container networking, IAM execution-role permissions, PostgreSQL connectivity, and runtime behavior still need validation in real AWS.

## Try the document API

Upload a PDF, CSV, or XLSX file (maximum 10 MiB by default):

```powershell
curl.exe -u username -F "file=@invoice.pdf" http://127.0.0.1:8000/api/documents/
```

The API requires a Django account; `curl.exe -u username` prompts for its password.

The response includes its UUID, metadata, initial `pending` status, and a short-lived `download_url`. The worker changes status to `processed` after extracting invoice fields from a supported PDF. List documents or retrieve one by its UUID to see status, extracted fields, and retry details:

```powershell
curl.exe -u username http://127.0.0.1:8000/api/documents/
curl.exe -u username http://127.0.0.1:8000/api/documents/<document-uuid>/
```

Open the returned `download_url` to fetch the stored object. Delete a document and its S3 object with:

```powershell
curl.exe -u username -X DELETE http://127.0.0.1:8000/api/documents/<document-uuid>/
```

## Configuration

Edit `.env` for local settings. It is ignored by Git. Generate a private `SECRET_KEY` with `python -c "import secrets; print(secrets.token_urlsafe(50))"` before exposing Django beyond localhost. The AWS credentials in `.env.example` are dummy values accepted by local emulators; never replace them with real credentials. Leave `AWS_ENDPOINT_URL=http://localhost:4566` for Floci. For AWS, leave access key variables unset and use an IAM role or secure environment configuration. Existing `.env` files using `AWS_S3_ENDPOINT_URL` continue to work.

`MAX_UPLOAD_SIZE` is in bytes (10 MiB by default). `AWS_S3_PRESIGNED_URL_TTL` is the download URL lifetime in seconds. `SQS_MAX_RECEIVE_COUNT` controls attempts before SQS moves a failing message to its dead-letter queue.

To inspect failed messages, receive one from the dead-letter queue:

```powershell
$dlqUrl = aws --endpoint-url http://localhost:4566 sqs get-queue-url --queue-name clouddoc-processing-dlq --query QueueUrl --output text
aws --endpoint-url http://localhost:4566 sqs receive-message --queue-url $dlqUrl --attribute-names All
```

Receiving makes the message temporarily invisible; it does not delete it. Use `delete-message` only after you have decided the failure is resolved.

## Stop services

```powershell
docker compose down
floci stop
```

PostgreSQL data remains in the `postgres_data` Docker volume. To delete that database data as well, use `docker compose down -v`.

## Scope and limitations

- The API and browser require authentication; document queries and download/delete routes are scoped to the signed-in owner.
- The extraction example uses text labels and regular expressions; it is not a general OCR or document-understanding system. Failed messages are retained in `clouddoc-processing-dlq` for inspection.
- Local HTTP Basic authentication is intended for development; use HTTPS and a production authentication setup before exposing the API.
- Floci behavior may differ from AWS. Validate AWS-specific behavior in the later deployment milestone.
