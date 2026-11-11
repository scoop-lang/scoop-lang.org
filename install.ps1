# Bootstrap scoop-install on Windows; installation arguments pass through unchanged.
#   irm https://scoop-lang.org/install.ps1 | iex
#   & ([scriptblock]::Create((irm https://scoop-lang.org/install.ps1))) --target x86_64-w64-windows-llvm-mingw-ucrt
# Keep this file ASCII-only for Windows PowerShell 5.1.

function Install-ScoopToolchain {
    param([string[]]$InstallArgs)
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'
    if ($PSVersionTable.PSVersion.Major -lt 5) { throw 'PowerShell 5.1 or later is required' }
    if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) {
        throw 'On macOS and Linux run: curl -fsSL https://scoop-lang.org/install.sh | sh'
    }
    $scoopArch = $env:PROCESSOR_ARCHITEW6432
    if (-not $scoopArch) { $scoopArch = $env:PROCESSOR_ARCHITECTURE }
    if ($scoopArch -ne 'AMD64') { throw "unsupported host: Windows/$scoopArch" }
    $scoopInstallRoot = $env:SCOOP_HOME
    if (-not $scoopInstallRoot) {
        if (-not $env:USERPROFILE) { throw 'USERPROFILE must be set' }
        $scoopInstallRoot = Join-Path $env:USERPROFILE '.scoop'
    }
    for ($i = 0; $i -lt $InstallArgs.Count; $i++) {
        $item = $InstallArgs[$i]
        if ($item -eq '--home') {
            if (++$i -ge $InstallArgs.Count) { throw '--home requires a directory' }
            $scoopInstallRoot = $InstallArgs[$i]
        } elseif ($item.StartsWith('--home=')) {
            $scoopInstallRoot = $item.Substring(7)
        } elseif ($item -in '--help', '-h') {
            Write-Host 'Usage: install.ps1 [VERSION] [--target TARGET] [--component gui,vendor] [--skip-docs] [--home DIR]'
            Write-Host 'All arguments are passed to scoop-install toolchain install.'
            Write-Host 'Set SCOOP_NO_MODIFY_PATH=1 to leave the user PATH unchanged.'
            return 0
        }
    }
    if (-not $scoopInstallRoot) { throw '--home requires a directory' }
    $scoopInstallRoot = [IO.Path]::GetFullPath($scoopInstallRoot)
    if ($PSVersionTable.PSEdition -ne 'Core') {
        # Let Windows negotiate current TLS versions, including TLS 1.3.
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::SystemDefault
    }
    $scoopUrl = $env:SCOOP_INSTALL_URL
    if (-not $scoopUrl) {
        $scoopUrl = 'https://release.scoop-lang.org/installers/0.1.0/scoop-install-x86_64-pc-windows-gnullvm.exe'
    }
    $scoopDownloadDir = Join-Path $scoopInstallRoot ('tmp\bootstrap.' + [IO.Path]::GetRandomFileName())
    New-Item -ItemType Directory -Force -Path $scoopDownloadDir | Out-Null
    try {
        $scoopManager = Join-Path $scoopDownloadDir 'scoop-install.exe'
        Write-Host 'Downloading scoop-install for Windows x64...'
        Get-ScoopFile $scoopUrl $scoopManager
        & $scoopManager toolchain install @InstallArgs | Out-Host
        if ($LASTEXITCODE -ne 0) { return $LASTEXITCODE }
        $scoopBin = Join-Path $scoopInstallRoot 'bin'
        if ($env:SCOOP_NO_MODIFY_PATH -ne '1') { Add-ScoopUserPath $scoopBin }
        if (-not (Test-ScoopPathContains $env:Path $scoopBin)) { $env:Path = "$scoopBin;$env:Path" }
        Write-Host "Scoop is installed in $scoopInstallRoot."
        Write-Host 'This PowerShell session can run sco now; open a new terminal elsewhere.'
        Write-Host 'Use scoop-install update to retain your selected targets and components.'
        return 0
    } finally {
        Remove-Item -LiteralPath $scoopDownloadDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Get-ScoopFile([string]$Url, [string]$OutFile) {
    for ($scoopAttempt = 1; ; $scoopAttempt++) {
        try {
            Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
            return
        } catch {
            if ($scoopAttempt -ge 4) { throw }
            Start-Sleep -Seconds $scoopAttempt
        }
    }
}

function Test-ScoopPathContains([string]$PathValue, [string]$Directory) {
    $scoopWanted = $Directory.TrimEnd('\')
    foreach ($scoopEntry in ($PathValue -split ';')) {
        if (-not $scoopEntry) { continue }
        $scoopExpanded = [Environment]::ExpandEnvironmentVariables($scoopEntry).TrimEnd('\')
        if ($scoopExpanded -ieq $scoopWanted) { return $true }
    }
    return $false
}

function Add-ScoopUserPath([string]$Directory) {
    # Edit the registry value directly so %VARIABLE% references in the user PATH stay unexpanded.
    $scoopKey = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
    try {
        $scoopPath = [string]$scoopKey.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        if (Test-ScoopPathContains $scoopPath $Directory) { return }
        if ($scoopPath) { $scoopPath = "$Directory;$scoopPath" } else { $scoopPath = $Directory }
        $scoopKey.SetValue('Path', $scoopPath, [Microsoft.Win32.RegistryValueKind]::ExpandString)
    } finally {
        $scoopKey.Close()
    }
    # Setting a user variable broadcasts WM_SETTINGCHANGE, so Explorer and new terminals see the PATH.
    [Environment]::SetEnvironmentVariable('SCOOP_INSTALL_PATH_REFRESH', '1', 'User')
    [Environment]::SetEnvironmentVariable('SCOOP_INSTALL_PATH_REFRESH', $null, 'User')
    Write-Host "Added $Directory to the user PATH"
}

# Do not exit an interactive irm | iex session on an installation error.
$scoopInstallExit = 1
try {
    $scoopInstallExit = Install-ScoopToolchain -InstallArgs @($args)
} catch {
    [Console]::Error.WriteLine("Error: $($_.Exception.Message)")
}
$global:LASTEXITCODE = $scoopInstallExit
if ($scoopInstallExit -ne 0 -and $PSCommandPath) { exit $scoopInstallExit }
