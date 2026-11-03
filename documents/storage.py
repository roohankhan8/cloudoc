import boto3
from botocore.config import Config
from django.conf import settings


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        config=Config(s3={"addressing_style": "path"}),
    )


def upload_document(file_obj, object_key):
    s3_client().upload_fileobj(
        file_obj,
        settings.AWS_S3_BUCKET_NAME,
        object_key,
        ExtraArgs={"ContentType": file_obj.content_type or "application/octet-stream"},
    )


def delete_document(object_key):
    s3_client().delete_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=object_key)


def create_download_url(object_key):
    return s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": object_key},
        ExpiresIn=settings.AWS_S3_PRESIGNED_URL_TTL,
    )
