# CloudDoc

CloudDoc is a Django REST API learning project for storing and processing documents with PostgreSQL and AWS services. Milestones 1-3 cover the Floci/AWS CLI S3 exercise, the Django document API, and asynchronous SQS processing.

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

## Try the document API

Upload a PDF, CSV, or XLSX file (maximum 10 MiB by default):

```powershell
curl.exe -F "file=@invoice.pdf" http://127.0.0.1:8000/api/documents/
```

The response includes its UUID, metadata, initial `pending` status, and a short-lived `download_url`. The worker changes status to `processed` after checking that the S3 object exists. List documents or retrieve one by its UUID to see status and retry details:

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

- The API implements document upload, metadata, presigned downloads, deletion, and queued processing status. It does not add authentication, ownership checks, or document extraction.
- The worker currently verifies the object in S3; document extraction begins in Milestone 4. Failed messages are retained in `clouddoc-processing-dlq` for inspection.
- The API has no authentication yet. Keep the development server bound to localhost and do not expose it to a network.
- Floci behavior may differ from AWS. Validate AWS-specific behavior in the later deployment milestone.
