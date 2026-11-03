from django.conf import settings

from .aws import aws_client


def s3_client():
    return aws_client("s3")


def upload_document(file_obj, object_key):
    s3_client().upload_fileobj(
        file_obj,
        settings.AWS_S3_BUCKET_NAME,
        object_key,
        ExtraArgs={"ContentType": file_obj.content_type or "application/octet-stream"},
    )


def delete_document(object_key):
    s3_client().delete_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=object_key)


def verify_document_exists(object_key):
    s3_client().head_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=object_key)


def create_download_url(object_key):
    return s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": object_key},
        ExpiresIn=settings.AWS_S3_PRESIGNED_URL_TTL,
    )
