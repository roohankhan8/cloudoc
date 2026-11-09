output "document_bucket_name" {
  value = aws_s3_bucket.documents.bucket
}

output "processing_queue_url" {
  value = aws_sqs_queue.processing.url
}

output "processing_queue_arn" {
  value = aws_sqs_queue.processing.arn
}

output "dead_letter_queue_url" {
  value = aws_sqs_queue.dead_letter.url
}

output "api_policy_arn" {
  value = aws_iam_policy.api.arn
}

output "processor_policy_arn" {
  value = aws_iam_policy.processor.arn
}

output "processor_role_arn" {
  value = aws_iam_role.processor.arn
}
