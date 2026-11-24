; Inno Setup 6/7 installer for MARCOS IDE 31.0.0.
; The build script supplies a SignTool when a trusted signing certificate is configured.
#define AppName "MARCOS IDE 31.0"
#define AppVersion "31.0.0"
#define AppPublisher "Marcos Tech Innovations"
#define AppExeName "MARCOS_IDE.exe"

[Setup]
AppId={{E8A0B611-7B86-4B6C-9278-8F7A8D080017}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\MARCOS IDE 31.0
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=release
OutputBaseFilename=MARCOS_IDE_31.0.0_Setup
SetupLogging=yes
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\{#AppExeName}
VersionInfoVersion=31.0.0.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Ambiente de desenvolvimento da Linguagem MARCOS
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
SignedUninstaller=yes
SignTool=MarcosCodeSign

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"

[Files]
Source: "dist\MARCOS_IDE.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "CONFIGURAR_IA_WINDOWS.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LEIA_PRIMEIRO.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "marcos_engine.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "marcosc.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements-build.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements-ml.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements-dl.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements-advanced-ai.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements-finetune.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements-onnxruntime.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "gerar_exe_windows.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "exemplos\*.mar"; DestDir: "{app}\exemplos"; Flags: ignoreversion
Source: "exemplos\*.jsonl"; DestDir: "{app}\exemplos"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\MARCOS IDE 31.0"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\MARCOS IDE 31.0"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Abrir MARCOS IDE 31.0"; Flags: postinstall nowait skipifsilent
