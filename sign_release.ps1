param(
    [Parameter(Mandatory = $true)]
    [string]$CertificateThumbprint,
    [string[]]$Files = @("dist\MARCOS_IDE.exe", "release\MARCOS_IDE_31.0.0_Setup.exe"),
    [string]$TimestampUrl = "https://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$SignTool = Get-Command signtool.exe -ErrorAction Stop
$Thumb = ($CertificateThumbprint -replace "\s", "").ToUpperInvariant()
$Cert = Get-ChildItem Cert:\CurrentUser\My, Cert:\LocalMachine\My |
    Where-Object { $_.Thumbprint -eq $Thumb } |
    Select-Object -First 1

if (-not $Cert) {
    throw "Certificado $Thumb não foi encontrado no repositório de certificados do Windows."
}
if (-not $Cert.HasPrivateKey) {
    throw "O certificado selecionado não possui chave privada disponível."
}

foreach ($RelativeFile in $Files) {
    $FullPath = Join-Path $Root $RelativeFile
    if (-not (Test-Path $FullPath)) { throw "Arquivo não encontrado: $FullPath" }

    & $SignTool.Source sign /sha1 $Thumb /s My /fd SHA256 /tr $TimestampUrl /td SHA256 $FullPath
    if ($LASTEXITCODE -ne 0) { throw "Falha ao assinar: $FullPath" }

    & $SignTool.Source verify /pa /v $FullPath
    if ($LASTEXITCODE -ne 0) { throw "Falha na validação da assinatura: $FullPath" }

    Write-Host "Assinatura válida: $FullPath" -ForegroundColor Green
}
