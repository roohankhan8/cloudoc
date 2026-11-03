# CloudDoc

CloudDoc is a Django REST API learning project for storing and processing documents with PostgreSQL and AWS services. Milestone 1 covers the Floci/AWS CLI S3 exercise; this milestone adds a local Django API that stores document objects in S3 and metadata in PostgreSQL.

See [the project plan](docs/PROJECT_PLAN.md) and [the original roadmap](CloudDoc_AWS_Floci_Project_Roadmap.md).

## Requirements

- Windows with PowerShell
- Python 3.12+
- Docker Desktop running Linux containers
- Floci CLI, AWS CLI v2

## Start the local services

From the project folder, create a local environment file and start Floci:

```powershell
Copy-Item .env.example .env
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

The Django server runs on your Windows host and connects to PostgreSQL on `127.0.0.1:5432` and Floci on `localhost:4566`.

## Install and run Django

Activate the existing virtual environment, or create one if needed:

```powershell
if (-not (Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create the database tables and start the API:

```powershell
python manage.py migrate
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/documents/`.

## Try the document API

Upload a PDF, CSV, or XLSX file (maximum 10 MiB by default):

```powershell
curl.exe -F "file=@invoice.pdf" http://127.0.0.1:8000/api/documents/
```

The response includes its UUID, metadata, and a short-lived `download_url`. List documents or retrieve one by its UUID:

```powershell
curl.exe http://127.0.0.1:8000/api/documents/
curl.exe http://127.0.0.1:8000/api/documents/<document-uuid>/
```

Open the returned `download_url` to fetch the stored object. Delete a document and its S3 object with:

```powershell
curl.exe -X DELETE http://127.0.0.1:8000/api/documents/<document-uuid>/
```

## Configuration

Edit `.env` for local settings. It is ignored by Git. The included AWS credentials are dummy values accepted by local emulators; never replace them with real credentials. Leave `AWS_S3_ENDPOINT_URL=http://localhost:4566` for Floci. For a later AWS environment, use an empty endpoint and real credentials from an IAM role or secure environment configuration.

`MAX_UPLOAD_SIZE` is in bytes (10 MiB by default). `AWS_S3_PRESIGNED_URL_TTL` is the download URL lifetime in seconds.

## Stop services

```powershell
docker compose down
floci stop
```

PostgreSQL data remains in the `postgres_data` Docker volume. To delete that database data as well, use `docker compose down -v`.

## Scope and limitations

- This milestone implements document upload, metadata, presigned downloads, and deletion. It does not add authentication, ownership checks, queues, workers, or extraction.
- The API has no authentication yet. Keep the development server bound to localhost and do not expose it to a network.
- Floci behavior may differ from AWS. Validate AWS-specific behavior in the later deployment milestone.
