; Medical Spytool Inno Setup Script
; Erstellt ein vollständiges Installationsprogramm für Windows-Benutzer

#define MyAppName "Medical Spytool"
#define MyAppVersion "2.0"
#define MyAppPublisher "Medizinische Fakultät"
#define MyAppURL "https://www.example.com/medicalspytool"
#define MyAppExeName "RunMedicalSpytool.bat"
#define MyAppIconName "generated-icon.png"

[Setup]
; Grundeinstellungen für das Installationsprogramm
AppId={{4F53D992-B5A4-40E0-BB01-04A5B8C5A561}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Benötigte Admin-Rechte für Python-Installation
PrivilegesRequired=admin
OutputBaseFilename=MedicalSpytool_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Alle Projektdateien kopieren (außer .git, __pycache__ und temporäre Dateien)
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".git,__pycache__,*.pyc,*.log,venv,warnings.log"
; Spezielle Hinzufügung des Icons
Source: "generated-icon.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppIconName}"

[Run]
; Führt nach der Installation die Initialisierung durch
Filename: "{app}\INSTALLATION.bat"; Description: "Python-Abhängigkeiten installieren und einrichten"; Flags: runascurrentuser
; Bietet an, die Anwendung nach der Installation zu starten
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Überprüft, ob Python installiert ist
function IsPythonInstalled: Boolean;
var
  PythonInstalled: Boolean;
  ResultCode: Integer;
begin
  // Prüft, ob Python verfügbar ist
  PythonInstalled := False;
  if Exec(ExpandConstant('{cmd}'), '/C python --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
      PythonInstalled := True;
  end;
  Result := PythonInstalled;
end;

// Führt vor der Installation aus
function InitializeSetup: Boolean;
var
  PythonInstalled: Boolean;
  MsgResult: Integer;
begin
  Result := True;
  
  // Prüft, ob Python installiert ist
  PythonInstalled := IsPythonInstalled();
  
  if not PythonInstalled then
  begin
    MsgResult := MsgBox('Python wurde nicht gefunden. Python 3.8 oder höher ist für Medical Spytool erforderlich.' + #13#10 +
                       'Möchten Sie jetzt Python herunterladen und installieren?', mbConfirmation, MB_YESNO);
                       
    if MsgResult = IDYES then
    begin
      ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOW, ewNoWait, ResultCode);
      MsgBox('Bitte installieren Sie Python und stellen Sie sicher, dass "Add Python to PATH" aktiviert ist.' + #13#10 +
            'Führen Sie danach dieses Installationsprogramm erneut aus.', mbInformation, MB_OK);
      Result := False;
    end
    else
    begin
      MsgBox('Python ist für Medical Spytool erforderlich. Die Installation wird fortgesetzt, ' +
            'aber die Anwendung wird nicht funktionieren, bis Python installiert ist.', mbInformation, MB_OK);
    end;
  end;
end;
