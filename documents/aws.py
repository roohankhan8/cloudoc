import boto3
from botocore.config import Config
from django.conf import settings


def aws_client(service_name):
    return boto3.client(
        service_name,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        config=Config(s3={"addressing_style": "path"}) if service_name == "s3" else Config(),
    )
