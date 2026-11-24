param(
    [switch]$SkipInstall,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not $IsWindows -and $env:OS -ne "Windows_NT") {
    throw "O build da MARCOS IDE 31.0 precisa ser executado no Windows."
}

$Python = (Get-Command python -ErrorAction Stop).Source
if (-not $SkipInstall) {
    & $Python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar pip." }
    & $Python -m pip install -r requirements.txt -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências." }
}

Write-Host "Executando testes automatizados..." -ForegroundColor Cyan
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Os testes falharam. Build cancelado." }

$Dist = Join-Path $Root "dist"
$Build = Join-Path $Root "build"
New-Item -ItemType Directory -Force -Path $Dist | Out-Null

Write-Host "Empacotando a aplicação desktop..." -ForegroundColor Cyan
$PyInstallerArgs = @(
    "--noconfirm", "--clean", "--onefile", "--windowed",
    "--name", "MARCOS_IDE",
    "--distpath", $Dist,
    "--workpath", $Build,
    "--specpath", $Build,
    "--paths", $Root,
    "--add-data", "static;static",
    "--hidden-import", "app",
    "--hidden-import", "marcos_engine",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols",
    "--hidden-import", "uvicorn.protocols.websockets",
    "--hidden-import", "uvicorn.protocols.websockets.auto",
    "--hidden-import", "uvicorn.lifespan",
    "--hidden-import", "uvicorn.lifespan.on",
    "--collect-all", "fastapi",
    "--collect-all", "starlette",
    "--collect-all", "uvicorn",
    "--collect-all", "websockets",
    "--collect-all", "pydantic",
    "--collect-all", "pydantic_core",
    "--collect-all", "anyio",
    "--version-file", (Join-Path $Root "version_info.txt"),
    (Join-Path $Root "desktop_launcher.py")
)
& $Python -m PyInstaller @PyInstallerArgs
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou." }

$AppExe = Join-Path $Dist "MARCOS_IDE.exe"
if (-not (Test-Path $AppExe)) { throw "Executável principal não foi criado." }

$SignThumbprint = $env:MARCOS_SIGN_CERT_THUMBPRINT
$SignTool = Get-Command signtool.exe -ErrorAction SilentlyContinue
if ($SignThumbprint) {
    if (-not $SignTool) { throw "signtool.exe não encontrado. Instale o Windows SDK." }
    Write-Host "Assinando executável principal..." -ForegroundColor Cyan
    & $SignTool.Source sign /sha1 $SignThumbprint /s My /fd SHA256 /tr "https://timestamp.digicert.com" /td SHA256 $AppExe
    if ($LASTEXITCODE -ne 0) { throw "Falha ao assinar MARCOS_IDE.exe." }
    & $SignTool.Source verify /pa /v $AppExe
    if ($LASTEXITCODE -ne 0) { throw "A assinatura do executável não foi validada." }
} else {
    Write-Warning "MARCOS_SIGN_CERT_THUMBPRINT não definido: build sem assinatura Authenticode."
}

if (-not $SkipInstaller) {
    $Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if (-not $Iscc) {
        $Candidates = @(
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe")
        )
        $Found = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
        if ($Found) { $IsccPath = $Found } else {
            throw "ISCC.exe não encontrado. Instale Inno Setup 6 ou 7."
        }
    } else {
        $IsccPath = $Iscc.Source
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $Root "release") | Out-Null
    $Iss = Join-Path $Root "MARCOS_IDE_30.iss"

    if ($SignThumbprint) {
        # /S is supported by Inno Setup 6 and 7.
        $SignCommand = "signtool.exe sign /sha1 $SignThumbprint /s My /fd SHA256 /tr https://timestamp.digicert.com /td SHA256 `$f"
        & $IsccPath "/SMarcosCodeSign=$SignCommand" $Iss
    } else {
        # Build an unsigned temporary script. This avoids relying on the
        # --no-signing option, which is only available in newer Inno versions.
        $UnsignedIss = Join-Path $Root "MARCOS_IDE_8.0_unsigned_build.iss"
        $IssContent = Get-Content -Raw -Path $Iss
        $IssContent = [regex]::Replace(
            $IssContent,
            '(?m)^SignTool=MarcosCodeSign\r?\n',
            ''
        )
        $IssContent = $IssContent.Replace("SignedUninstaller=yes", "SignedUninstaller=no")
        Set-Content -Path $UnsignedIss -Value $IssContent -Encoding UTF8
        try {
            & $IsccPath $UnsignedIss
        } finally {
            Remove-Item $UnsignedIss -Force -ErrorAction SilentlyContinue
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup não conseguiu compilar o instalador." }

    $SetupExe = Join-Path $Root "release\MARCOS_IDE_31.0.0_Setup.exe"
    if (-not (Test-Path $SetupExe)) { throw "Instalador não foi encontrado." }
    if ($SignThumbprint) {
        & $SignTool.Source verify /pa /v $SetupExe
        if ($LASTEXITCODE -ne 0) { throw "A verificação Authenticode do instalador falhou." }
    }
    Write-Host "Instalador criado: $SetupExe" -ForegroundColor Green
}

$ReleaseDir = Join-Path $Root "release"
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
$ReleaseFiles = @($AppExe)
$SetupPath = Join-Path $ReleaseDir "MARCOS_IDE_31.0.0_Setup.exe"
if (Test-Path $SetupPath) { $ReleaseFiles += $SetupPath }
$HashLines = foreach ($File in $ReleaseFiles) {
    $Hash = Get-FileHash -Algorithm SHA256 -Path $File
    "$($Hash.Hash)  $([IO.Path]::GetFileName($File))"
}
$HashLines | Set-Content -Path (Join-Path $Root "release\SHA256SUMS.txt") -Encoding ascii

Write-Host "Build concluído. Executável: $AppExe" -ForegroundColor Green
