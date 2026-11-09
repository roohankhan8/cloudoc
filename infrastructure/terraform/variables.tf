variable "aws_region" {
  description = "AWS region for CloudDoc resources."
  type        = string
  default     = "us-east-1"
}

variable "document_bucket_name" {
  description = "Globally unique S3 bucket name for uploaded documents."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for IAM policy names."
  type        = string
  default     = "clouddoc"
}

variable "lambda_function_name" {
  description = "Lambda function name whose CloudWatch logs the processor role may write."
  type        = string
  default     = "clouddoc-invoice-processor"
}

variable "processing_queue_name" {
  description = "SQS queue receiving document processing messages."
  type        = string
  default     = "clouddoc-processing"
}

variable "dead_letter_queue_name" {
  description = "SQS dead-letter queue name."
  type        = string
  default     = "clouddoc-processing-dlq"
}

variable "visibility_timeout_seconds" {
  description = "SQS visibility timeout for a processing message."
  type        = number
  default     = 30
}

variable "receive_wait_time_seconds" {
  description = "Long-poll wait time for SQS consumers."
  type        = number
  default     = 20
}

variable "max_receive_count" {
  description = "Receives before SQS moves a message to the dead-letter queue."
  type        = number
  default     = 3
}
