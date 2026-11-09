param(
    [string]$FunctionName = "clouddoc-invoice-processor",
    [string]$LambdaRoleArn,
    [string]$LambdaAwsEndpoint
)

$ErrorActionPreference = "Stop"
$null = Get-Command docker -ErrorAction Stop
$null = Get-Command aws -ErrorAction Stop
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$packagePrefix = $projectRoot.TrimEnd('\') + '\'

function Read-EnvFile($path, $values) {
    if (-not (Test-Path -LiteralPath $path)) { return }
    foreach ($line in Get-Content -LiteralPath $path) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
            $values[$Matches[1]] = $Matches[2].Trim('"', "'")
        }
    }
}

function Invoke-AwsCli([string[]]$Arguments) {
    $output = & aws @Arguments
    if ($LASTEXITCODE -ne 0) { throw "AWS CLI failed: aws $($Arguments -join ' ')" }
    return $output
}

$config = @{}
Read-EnvFile (Join-Path $projectRoot ".env.example") $config
Read-EnvFile (Join-Path $projectRoot ".env") $config
$awsEndpoint = $config["AWS_ENDPOINT_URL"]
if (-not $awsEndpoint) { $awsEndpoint = $config["AWS_S3_ENDPOINT_URL"] }
if (-not $awsEndpoint) { $awsEndpoint = "http://localhost:4566" }
if (-not $LambdaAwsEndpoint) {
    $endpointUri = [UriBuilder]$awsEndpoint
    if ($endpointUri.Host -in @("localhost", "127.0.0.1", "0.0.0.0")) {
        $endpointUri.Host = "host.docker.internal"
    }
    $LambdaAwsEndpoint = $endpointUri.Uri.AbsoluteUri.TrimEnd('/')
}
if (-not $LambdaRoleArn) {
    $LambdaRoleArn = $config["LAMBDA_ROLE_ARN"]
    if (-not $LambdaRoleArn) { $LambdaRoleArn = "arn:aws:iam::000000000000:role/lambda-role" }
}

$lambdaDbHost = $config["DB_HOST"]
if (-not $lambdaDbHost -or $lambdaDbHost -in @("localhost", "127.0.0.1", "0.0.0.0")) {
    $lambdaDbHost = "host.docker.internal"
}
$lambdaVariables = @{
        DEBUG = "False"
        DB_NAME = $(if ($config["DB_NAME"]) { $config["DB_NAME"] } else { "clouddoc" })
        DB_USER = $(if ($config["DB_USER"]) { $config["DB_USER"] } else { "clouddoc" })
        DB_PASSWORD = $(if ($config["DB_PASSWORD"]) { $config["DB_PASSWORD"] } else { "clouddoc" })
        DB_HOST = $lambdaDbHost
        DB_PORT = $(if ($config["DB_PORT"]) { $config["DB_PORT"] } else { "5434" })
        AWS_ACCESS_KEY_ID = $config["AWS_ACCESS_KEY_ID"]
        AWS_SECRET_ACCESS_KEY = $config["AWS_SECRET_ACCESS_KEY"]
        AWS_REGION = $(if ($config["AWS_REGION"]) { $config["AWS_REGION"] } else { "us-east-1" })
        AWS_ENDPOINT_URL = $LambdaAwsEndpoint
        AWS_S3_BUCKET_NAME = $(if ($config["AWS_S3_BUCKET_NAME"]) { $config["AWS_S3_BUCKET_NAME"] } else { "my-floci-bucket" })
        SQS_QUEUE_NAME = $(if ($config["SQS_QUEUE_NAME"]) { $config["SQS_QUEUE_NAME"] } else { "clouddoc-processing" })
        SQS_MAX_RECEIVE_COUNT = $(if ($config["SQS_MAX_RECEIVE_COUNT"]) { $config["SQS_MAX_RECEIVE_COUNT"] } else { "3" })
    }
foreach ($credential in @("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")) {
    if ([string]::IsNullOrWhiteSpace($lambdaVariables.$credential)) {
        $lambdaVariables.Remove($credential)
    }
}
$lambdaEnv = @{ Variables = $lambdaVariables } | ConvertTo-Json -Compress

$archivePath = Join-Path $projectRoot "clouddoc-lambda.zip"
$archivePath = [System.IO.Path]::GetFullPath($archivePath)
if (-not $archivePath.StartsWith($packagePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Lambda archive path must stay inside the project folder."
}
$packageCommand = 'python -m pip install --no-cache-dir -r /var/task/requirements-lambda.txt -t /tmp/lambda-package && python -c ''import os,zipfile; z=zipfile.ZipFile("/var/task/clouddoc-lambda.zip","w",zipfile.ZIP_DEFLATED); roots=[("/tmp/lambda-package","/tmp/lambda-package"),("/var/task/config","/var/task"),("/var/task/documents","/var/task")]; [z.write(os.path.join(root,f),os.path.relpath(os.path.join(root,f),prefix)) for base,prefix in roots for root,_,files in os.walk(base) for f in files if not f.endswith(".pyc") and "__pycache__" not in root]; z.close()'''
& docker run --rm --entrypoint /bin/sh -v "${projectRoot}:/var/task" public.ecr.aws/lambda/python:3.13 -c $packageCommand
if ($LASTEXITCODE -ne 0) { throw "Could not install Lambda dependencies in the runtime container." }
Write-Output "Created $archivePath"

$awsRegion = $config["AWS_REGION"]
if (-not $awsRegion) { $awsRegion = "us-east-1" }
$awsPrefix = @("--endpoint-url", $awsEndpoint, "--region", $awsRegion, "lambda")
$functionResult = & aws @awsPrefix get-function --function-name $FunctionName --query "Configuration.FunctionName" --output text 2>&1
$functionExists = $LASTEXITCODE -eq 0
$functionError = $functionResult | Out-String
if (-not $functionExists -and $functionError -notmatch "ResourceNotFoundException|ResourceNotFound") {
    throw "Could not check Lambda function '$FunctionName': $functionError"
}
if ($functionExists) {
    Invoke-AwsCli ($awsPrefix + @("update-function-code", "--function-name", $FunctionName, "--zip-file", "fileb://$archivePath")) | Out-Null
    Invoke-AwsCli ($awsPrefix + @("wait", "function-updated-v2", "--function-name", $FunctionName)) | Out-Null
    Invoke-AwsCli ($awsPrefix + @("update-function-configuration", "--function-name", $FunctionName, "--timeout", "60", "--memory-size", "512", "--environment", $lambdaEnv)) | Out-Null
    Write-Output "Updated Lambda function $FunctionName"
} else {
    Invoke-AwsCli ($awsPrefix + @("create-function", "--function-name", $FunctionName, "--runtime", "python3.13", "--role", $LambdaRoleArn, "--handler", "documents.lambda_handler.handler", "--zip-file", "fileb://$archivePath", "--timeout", "60", "--memory-size", "512", "--environment", $lambdaEnv)) | Out-Null
    Write-Output "Created Lambda function $FunctionName"
}

$sqsPrefix = @("--endpoint-url", $awsEndpoint, "--region", $awsRegion, "sqs")
$queueName = $config["SQS_QUEUE_NAME"]
if (-not $queueName) { $queueName = "clouddoc-processing" }
$queueUrl = Invoke-AwsCli ($sqsPrefix + @("get-queue-url", "--queue-name", $queueName, "--query", "QueueUrl", "--output", "text"))
$queueArn = Invoke-AwsCli ($sqsPrefix + @("get-queue-attributes", "--queue-url", $queueUrl, "--attribute-names", "QueueArn", "--query", "Attributes.QueueArn", "--output", "text"))
$mappingPrefix = $awsPrefix + @("list-event-source-mappings", "--function-name", $FunctionName, "--event-source-arn", $queueArn, "--query", "EventSourceMappings[0].UUID", "--output", "text")
$mappingId = Invoke-AwsCli $mappingPrefix
if ($mappingId -and $mappingId -ne "None") {
    Invoke-AwsCli ($awsPrefix + @("update-event-source-mapping", "--uuid", $mappingId, "--enabled", "--batch-size", "10", "--function-response-types", "ReportBatchItemFailures")) | Out-Null
    Write-Output "Updated SQS event mapping $mappingId"
} else {
    Invoke-AwsCli ($awsPrefix + @("create-event-source-mapping", "--function-name", $FunctionName, "--event-source-arn", $queueArn, "--batch-size", "10", "--function-response-types", "ReportBatchItemFailures")) | Out-Null
    Write-Output "Connected $queueName to $FunctionName"
}

Write-Output "Lambda deployment complete. Keep the local process_documents worker stopped."
