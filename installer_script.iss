; Inno Setup 安装脚本
; Image Stitcher 安装程序

#define AppName "Image Stitcher"
#define AppVersion "1.0.0"
#define AppPublisher "Image Stitcher"
#define AppExeName "ImageStitcher.exe"
#define AppPublisherURL "https://github.com/yourusername/Image-Stitcher"
#define AppSupportURL "https://github.com/yourusername/Image-Stitcher/issues"

[Setup]
; 应用程序基本信息
AppId={{A1B2C3D4-E5F6-4A5B-8C7D-1E2F3A4B5C6E}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppPublisherURL}
AppSupportURL={#AppSupportURL}
AppUpdatesURL={#AppPublisherURL}

; 默认安装目录
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}

; 输出文件名和压缩设置
OutputBaseFilename=ImageStitcher-Setup
OutputDir=installer_output
Compression=lzma2/max
SolidCompression=yes

; 程序相关设置
DisableDirPage=no
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableFinishedPage=no

; 权限要求（建议管理员权限）
PrivilegesRequired=admin

; 安装程序图标和样式
SetupIconFile=assets\icon.ico
WizardStyle=modern
ShowLanguageDialog=no

; 生成卸载程序
UninstallDisplayIcon={app}\{#AppExeName}
UninstallFilesDir={app}

[Languages]
Name: "default"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 安装所有文件
Source: "dist\ImageStitcher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 创建开始菜单快捷方式
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}"

; 创建桌面快捷方式（根据用户选择）
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后运行程序
Filename: "{app}\{#AppExeName}"; Description: "启动 {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时删除用户数据目录（可选）
; Type: filesandordirs; Name: "{userappdata}\{#AppName}"
