$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$packagePath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot ".lambda-package"))
$packagePrefix = $projectRoot.TrimEnd('\') + '\'
if (-not $packagePath.StartsWith($packagePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Lambda package path must stay inside the project folder."
}

if (Test-Path -LiteralPath $packagePath) {
    Remove-Item -LiteralPath $packagePath -Recurse -Force
}
New-Item -ItemType Directory -Path $packagePath | Out-Null

docker run --rm --entrypoint /bin/sh -v "${projectRoot}:/var/task" public.ecr.aws/lambda/python:3.13 -c "python -m pip install --no-cache-dir -r /var/task/requirements-lambda.txt -t /var/task/.lambda-package"
if ($LASTEXITCODE -ne 0) { throw "Could not install Lambda dependencies in the runtime container." }

Copy-Item -LiteralPath (Join-Path $projectRoot "config") -Destination $packagePath -Recurse
Copy-Item -LiteralPath (Join-Path $projectRoot "documents") -Destination $packagePath -Recurse

$archivePath = Join-Path $projectRoot "clouddoc-lambda.zip"
if (Test-Path -LiteralPath $archivePath) { Remove-Item -LiteralPath $archivePath -Force }
Compress-Archive -Path (Join-Path $packagePath "*") -DestinationPath $archivePath
Write-Output "Created $archivePath"
