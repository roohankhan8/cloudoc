# CloudDoc

CloudDoc is a Django learning project for uploading invoices, extracting a few fields, and processing them asynchronously with PostgreSQL and AWS services. Milestones 1-4 cover local Floci setup, the Django document interface/API, SQS, and invoice extraction with a local worker or Lambda.

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

Start the API in one PowerShell window:

```powershell
python manage.py runserver
```

Start the worker in a second window with the virtual environment activated:

```powershell
python manage.py process_documents
```

The frontend is available at `http://127.0.0.1:8000/`; the API remains available at `http://127.0.0.1:8000/api/documents/`.

## Invoice extraction

The worker extracts `invoice_number`, `invoice_date`, and `total_amount` from text-based PDFs and saves them in PostgreSQL. Results appear in the frontend and document API response. Use labels such as `Invoice Number: INV-1001`, `Invoice Date: 2026-01-15`, and `Total: USD 125.00`. Image-only scans need OCR, which this milestone does not include. CSV and XLSX uploads are still accepted, but extraction currently supports PDFs only.

Sample invoices for testing are in [`output/pdf/`](output/pdf/):

- [USD invoice](output/pdf/sample-invoice-usd.pdf): `INV-2026-001`, `2026-11-04`, `USD 1,249.50`
- [PKR invoice](output/pdf/sample-invoice-pkr.pdf): `INV-2026-002`, `2026-10-28`, `PKR 48,750.00`
- [Minimal invoice](output/pdf/sample-invoice-minimal.pdf): `INV-2026-003`, `2026-09-15`, `USD 89.99`

## Run the same processor through Lambda

Stop the local `process_documents` worker first so it does not consume messages alongside Lambda. Package the function using the Lambda Python runtime image:

```powershell
.\scripts\package_lambda.ps1
```

Create a local function. The sample database values below match `.env.example`; adjust them if your local database uses different credentials. `host.docker.internal` lets the Lambda container reach PostgreSQL running on the Windows host. Floci supplies the Lambda container's reachable AWS endpoint.

```powershell
$lambdaEnvironment = @{
  Variables = @{
    DEBUG = "False"
    DB_NAME = "clouddoc"
    DB_USER = "clouddoc"
    DB_PASSWORD = "clouddoc"
    DB_HOST = "host.docker.internal"
    DB_PORT = "5434"
    AWS_ACCESS_KEY_ID = "test"
    AWS_SECRET_ACCESS_KEY = "test"
    AWS_REGION = "us-east-1"
    AWS_S3_BUCKET_NAME = "my-floci-bucket"
    SQS_MAX_RECEIVE_COUNT = "3"
  }
} | ConvertTo-Json -Compress

aws --endpoint-url http://localhost:4566 lambda create-function `
  --function-name clouddoc-invoice-processor `
  --runtime python3.13 `
  --role arn:aws:iam::000000000000:role/lambda-role `
  --handler documents.lambda_handler.handler `
  --zip-file fileb://clouddoc-lambda.zip `
  --timeout 60 `
  --memory-size 512 `
  --environment $lambdaEnvironment
```

Connect the function to the existing SQS queue. Partial batch failure reporting lets SQS retry failed messages and eventually route them to the configured dead-letter queue.

```powershell
$queueUrl = aws --endpoint-url http://localhost:4566 sqs get-queue-url --queue-name clouddoc-processing --query QueueUrl --output text
$queueArn = aws --endpoint-url http://localhost:4566 sqs get-queue-attributes --queue-url $queueUrl --attribute-names QueueArn --query Attributes.QueueArn --output text
aws --endpoint-url http://localhost:4566 lambda create-event-source-mapping --function-name clouddoc-invoice-processor --event-source-arn $queueArn --batch-size 10 --function-response-types ReportBatchItemFailures
```

Upload a PDF from the frontend and watch its status/results update. To return to local-worker mode, remove the Lambda event source mapping before restarting `python manage.py process_documents`. Use `aws lambda list-event-source-mappings` to find its UUID, then `aws lambda delete-event-source-mapping --uuid <uuid>` to remove it.

This demonstrates local event-mapping behavior described in the [Floci Lambda guide](https://floci.io/floci/services/lambda/). Lambda container networking, IAM execution-role permissions, PostgreSQL connectivity, and runtime behavior still need validation in real AWS.

## Try the document API

Upload a PDF, CSV, or XLSX file (maximum 10 MiB by default):

```powershell
curl.exe -F "file=@invoice.pdf" http://127.0.0.1:8000/api/documents/
```

The response includes its UUID, metadata, initial `pending` status, and a short-lived `download_url`. The worker changes status to `processed` after extracting invoice fields from a supported PDF. List documents or retrieve one by its UUID to see status, extracted fields, and retry details:

```powershell
curl.exe http://127.0.0.1:8000/api/documents/
curl.exe http://127.0.0.1:8000/api/documents/<document-uuid>/
```

Open the returned `download_url` to fetch the stored object. Delete a document and its S3 object with:

```powershell
curl.exe -X DELETE http://127.0.0.1:8000/api/documents/<document-uuid>/
```

## Configuration

Edit `.env` for local settings. It is ignored by Git. The included AWS credentials are dummy values accepted by local emulators; never replace them with real credentials. Leave `AWS_ENDPOINT_URL=http://localhost:4566` for Floci. For a later AWS environment, use an empty endpoint and real credentials from an IAM role or secure environment configuration. Existing `.env` files using `AWS_S3_ENDPOINT_URL` continue to work.

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

- The API implements document upload, metadata, presigned downloads, deletion, queued processing status, and basic invoice extraction. It does not add authentication or ownership checks.
- The extraction example uses text labels and regular expressions; it is not a general OCR or document-understanding system. Failed messages are retained in `clouddoc-processing-dlq` for inspection.
- The API has no authentication yet. Keep the development server bound to localhost and do not expose it to a network.
- Floci behavior may differ from AWS. Validate AWS-specific behavior in the later deployment milestone.
