import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from documents.aws import aws_client
from documents.models import Document
from documents.queue import queue_url


def main():
    bucket = django.conf.settings.AWS_S3_BUCKET_NAME
    s3 = aws_client("s3")
    sqs = aws_client("sqs")
    user = get_user_model().objects.create_user(username=f"ci-{uuid.uuid4().hex}")
    client = APIClient()
    client.defaults["HTTP_HOST"] = "localhost"
    client.force_authenticate(user)
    message = None
    document = None
    document_id = None
    bucket_created = False

    try:
        s3.create_bucket(Bucket=bucket)
        bucket_created = True
        with open("output/pdf/sample-invoice-minimal.pdf", "rb") as sample:
            response = client.post(
                "/api/documents/",
                {"file": SimpleUploadedFile("sample.pdf", sample.read(), content_type="application/pdf")},
                format="multipart",
            )
        assert response.status_code == 201, getattr(response, "data", response.content)
        document_id = response.data["id"]
        document = Document.objects.get(pk=document_id, owner=user)
        assert s3.get_object(Bucket=bucket, Key=document.object_key)["Body"].read()

        received = sqs.receive_message(QueueUrl=queue_url(), MaxNumberOfMessages=1, WaitTimeSeconds=1)
        message = received["Messages"][0]
        assert json.loads(message["Body"])["document_id"] == str(document.id)
        sqs.delete_message(QueueUrl=queue_url(), ReceiptHandle=message["ReceiptHandle"])
        message = None

        assert client.delete(f"/api/documents/{document.id}/").status_code == 204
        document = None
        print("Floci upload, S3 storage, and SQS enqueue smoke check passed.")
    finally:
        if message:
            sqs.delete_message(QueueUrl=queue_url(), ReceiptHandle=message["ReceiptHandle"])
        if document is None and document_id:
            document = Document.objects.filter(pk=document_id).first()
        if document:
            s3.delete_object(Bucket=bucket, Key=document.object_key)
            document.delete()
        if bucket_created:
            s3.delete_bucket(Bucket=bucket)
        user.delete()


if __name__ == "__main__":
    main()
