; Script de Instalação Profissional Inno Setup 6 para ELOS DO VAZIO
; Desenvolvido para a Exposição / Apresentação Pública

#define MyAppName "Elos do Vazio"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "GoDev Studio"
#define MyAppExeName "Elos_do_Vazio.exe"

[Setup]
; Identificador único da aplicação (GUID gerado para Elos do Vazio)
AppId={{5A8D2F31-9F1C-4B7C-A583-6C789E23B89D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/
AppSupportURL=https://github.com/
AppUpdatesURL=https://github.com/
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Permite instalar sem privilégios de administrador em máquinas de exposição/escola
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline dialog
OutputDir=..\dist_installer
OutputBaseFilename=Instalador_Elos_do_Vazio_Inno
SetupIconFile=..\assets\icone_jogo.ico
WizardStyle=modern
WizardImageFile=installer_assets\wizard_side.bmp
WizardSmallImageFile=installer_assets\wizard_small.bmp
Compression=lzma2/ultra64
SolidCompression=yes
InfoBeforeFile=..\docs\LEIA-ME.txt

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "..\dist\Elos_do_Vazio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\assets\icone_jogo.ico"
Name: "{group}\Guia da Exposição (LEIA-ME)"; Filename: "{app}\_internal\LEIA-ME.txt"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\assets\icone_jogo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

