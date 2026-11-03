#!/bin/bash

ENDPOINT="http://localhost:4566"
BUCKET_NAME="my-floci-bucket"

# Check if the bucket list is empty
if [ -z "$(aws --endpoint-url=$ENDPOINT s3 ls)" ]; then
    echo "No buckets found. Creating '$BUCKET_NAME'..."
    aws --endpoint-url=$ENDPOINT s3 mb s3://$BUCKET_NAME
    echo "Bucket created successfully."
    # Verification: check that the bucket now appears in the list
    aws --endpoint-url=$ENDPOINT s3 ls
else
    echo "Buckets already exist in Floci."
    aws --endpoint-url=$ENDPOINT s3 ls
fi