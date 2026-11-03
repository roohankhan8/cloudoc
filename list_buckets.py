import boto3
from botocore.exceptions import ClientError

# Create an S3 client pointing to your local Floci instance
s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='floci',
    aws_secret_access_key='floci',
    region_name='us-east-1'
)

bucket_name = 'my-floci-bucket'

try:
    # Check if the bucket already exists and you have access to it
    s3_client.head_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' already exists.")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        print(f"Bucket '{bucket_name}' does not exist. Creating it now...")
        
        # Note: If your Floci region is us-east-1, create_bucket works without a LocationConstraint.
        # For other regions, you may need to pass CreateBucketConfiguration={'LocationConstraint': region_name}.
        s3_client.create_bucket(Bucket=bucket_name)
        
        print(f"Bucket '{bucket_name}' created successfully.")
        # *Verification:* Bucket is now present in `s3_client.list_buckets()`.
    else:
        print(f"An unexpected error occurred: {e}")