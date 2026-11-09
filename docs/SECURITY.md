# Security and permissions

## Application access

- Django login protects the browser; DRF requires an authenticated session or HTTP Basic credentials.
- Every new document records its owner. List, detail, download, and delete operations are filtered by that owner.
- Documents created before the ownership migration have a null owner and are hidden from users. Assign them deliberately through Django admin or discard them after confirming retention needs.
- Do not expose Django's development server or HTTP Basic authentication over an untrusted network. Use HTTPS and a production authentication configuration before deployment.
- `SECRET_KEY`, database passwords, and AWS credentials belong in ignored `.env` for local work or a secret manager/runtime environment in deployment. Do not commit `.env`.

## AWS IAM policy scope

Use separate roles for the API and processor. Replace account, region, bucket, and queue placeholders; scope object access to the application's bucket and queue. The API needs:

- `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` on `arn:aws:s3:::<bucket>/documents/*`.
- `sqs:GetQueueUrl`, `sqs:SendMessage` on the processing queue ARN.

The local worker needs:

- `s3:GetObject` on `arn:aws:s3:::<bucket>/documents/*`.
- `sqs:GetQueueUrl`, `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:ChangeMessageVisibility`, `sqs:GetQueueAttributes` on the processing queue ARN.

For the Lambda processor, its execution role needs the worker's S3 read permission and SQS consume permissions (`sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:ChangeMessageVisibility`, `sqs:GetQueueAttributes`) on the source queue, plus CloudWatch Logs write actions on its log group. Lambda's event source mapping also needs permission to poll the queue; grant that to the Lambda execution role as required by AWS. Keep deployment permissions (creating/updating Lambda and event source mappings, and passing the execution role) in a separate operator role.

No AWS IAM permission grants PostgreSQL access; configure database network access and credentials separately. Validate the exact policy and Lambda/SQS behavior in AWS because Floci does not provide a complete IAM boundary.
