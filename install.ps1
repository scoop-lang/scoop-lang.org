# Download and prepare the Scoop programming language toolchain on Windows.
#
#   irm https://scoop-lang.org/install.ps1 | iex
#   & ([scriptblock]::Create((irm https://scoop-lang.org/install.ps1))) -Release 2026-11-09 -- --jobs 2
#   powershell -ExecutionPolicy Bypass -File install.ps1 -NoModifyPath
#
# Pass post-install options (after --) with the script block form: Windows PowerShell 5.1
# -File treats "--" and "--name" arguments as parameter names and rejects them.
#
# Keep this file ASCII-only: Windows PowerShell 5.1 may decode a downloaded script
# with a legacy code page before Invoke-Expression runs it.
[CmdletBinding(PositionalBinding = $false)]
param(
    # A published release such as 2026-11-09; the latest release by default.
    [Alias('Version')]
    [string]$Release,
    # Do not add the install root's bin directory to the user PATH.
    [switch]$NoModifyPath,
    [switch]$Help,
    # Options passed through to post-install.ps1, for example -- --jobs 2.
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PostInstallArgs
)

function Install-ScoopToolchain {
    param([string]$Release, [bool]$NoModifyPath, [string[]]$PostInstallArgs)

    $ErrorActionPreference = 'Stop'
    # Invoke-WebRequest is very slow while it draws the progress bar.
    $ProgressPreference = 'SilentlyContinue'
    # Native command output goes to the host; the function's only output is the exit code.

    if ($PSVersionTable.PSVersion.Major -lt 5) {
        throw 'PowerShell 5.1 or later is required'
    }
    if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) {
        throw 'install.ps1 is for Windows; on macOS and Linux run: curl -fsSL https://scoop-lang.org/install.sh | sh'
    }
    $scoopArch = $env:PROCESSOR_ARCHITEW6432
    if (-not $scoopArch) { $scoopArch = $env:PROCESSOR_ARCHITECTURE }
    if ($scoopArch -ne 'AMD64') {
        throw "unsupported host: Windows/$scoopArch (the Windows release requires x86-64)"
    }
    if (-not $env:USERPROFILE) { throw 'USERPROFILE must be set' }

    if ($Release) {
        if ($Release -notmatch '^[A-Za-z0-9._-]+$' -or $Release.StartsWith('.')) {
            throw "invalid release name: $Release"
        }
    }
    # PowerShell normally consumes "--", but keep it out of post-install's options either way.
    $scoopPostArgs = @($PostInstallArgs | Where-Object { $null -ne $_ })
    if ($scoopPostArgs.Count -gt 0 -and $scoopPostArgs[0] -eq '--') {
        $scoopPostArgs = @($scoopPostArgs | Select-Object -Skip 1)
    }

    # Windows ships bsdtar; older builds lack xz support, so check before downloading.
    $scoopTar = Join-Path $env:SystemRoot 'System32\tar.exe'
    if (-not (Test-Path -LiteralPath $scoopTar)) {
        $scoopTarCommand = Get-Command tar.exe -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (-not $scoopTarCommand) { throw 'tar.exe is required (included with Windows 10 1803 and later)' }
        $scoopTar = $scoopTarCommand.Source
    }
    $scoopTarVersion = (& $scoopTar --version | Out-String)
    if ($scoopTarVersion -notmatch 'liblzma') {
        throw "$scoopTar cannot extract .tar.xz archives; update Windows or see https://scoop-lang.org/docs/install.html#manual-install"
    }

    if ($PSVersionTable.PSEdition -ne 'Core') {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor
            [Net.SecurityProtocolType]::Tls12
    }

    $scoopBaseUrl = $env:SCOOP_RELEASE_URL
    if (-not $scoopBaseUrl) { $scoopBaseUrl = 'https://release.scoop-lang.org' }
    $scoopBaseUrl = $scoopBaseUrl.TrimEnd('/')
    if ($Release) {
        $scoopIndexUrl = "$scoopBaseUrl/$Release/index.txt"
    } else {
        $scoopIndexUrl = "$scoopBaseUrl/latest.txt"
    }

    $scoopDownloadDir = Join-Path ([IO.Path]::GetTempPath()) ('scoop-install.' + [IO.Path]::GetRandomFileName())
    New-Item -ItemType Directory -Path $scoopDownloadDir | Out-Null
    try {
        try {
            Get-ScoopFile $scoopIndexUrl (Join-Path $scoopDownloadDir 'index.txt')
        } catch {
            throw "could not download the release index $scoopIndexUrl"
        }
        $scoopFormat = $null
        $scoopIndexRelease = $null
        $scoopVersion = $null
        $scoopPackages = @()
        foreach ($scoopLine in Get-Content -LiteralPath (Join-Path $scoopDownloadDir 'index.txt')) {
            $scoopFields = @($scoopLine.Trim() -split '\s+')
            switch ($scoopFields[0]) {
                'format' { $scoopFormat = $scoopFields[1] }
                'release' { $scoopIndexRelease = $scoopFields[1] }
                'version' { $scoopVersion = $scoopFields[1] }
                'package' {
                    if ($scoopFields[1] -ne 'windows') { continue }
                    $scoopPackage = $scoopFields[2]
                    if (-not $scoopPackage -or $scoopPackage.StartsWith('/') -or $scoopPackage.Contains('..') -or
                        $scoopPackage -notmatch '^[A-Za-z0-9._/+-]+$') {
                        throw "release index lists an invalid package: $scoopPackage"
                    }
                    $scoopPackages += $scoopPackage
                }
            }
        }
        if ($scoopFormat -ne '1') { throw "unsupported release index format at $scoopIndexUrl" }
        if (-not $scoopVersion -or $scoopVersion -notmatch '^[A-Za-z0-9.+-]+$') {
            throw "release index has an invalid version: $scoopVersion"
        }
        if ($scoopPackages.Count -eq 0) {
            throw ("Scoop packages for windows are not ready yet in release $scoopIndexRelease.`n" +
                'Please build Scoop from source: https://github.com/scoop-lang/scoop')
        }

        Write-Host "Downloading Scoop $scoopVersion (release $scoopIndexRelease) for windows..."
        $scoopStaging = Join-Path $scoopDownloadDir 'package'
        New-Item -ItemType Directory -Path $scoopStaging | Out-Null
        $scoopArchive = Join-Path $scoopDownloadDir 'archive.tar.xz'
        for ($scoopNumber = 1; $scoopNumber -le $scoopPackages.Count; $scoopNumber++) {
            $scoopPackage = $scoopPackages[$scoopNumber - 1]
            Write-Host ('[{0}/{1}] {2}' -f $scoopNumber, $scoopPackages.Count, ($scoopPackage -split '/')[-1])
            Get-ScoopFile "$scoopBaseUrl/$scoopPackage" $scoopArchive
            & $scoopTar -xJf $scoopArchive -C $scoopStaging | Out-Host
            if ($LASTEXITCODE -ne 0) { throw "could not extract $scoopPackage" }
            Remove-Item -LiteralPath $scoopArchive -Force
        }
        if (-not (Test-Path -LiteralPath (Join-Path $scoopStaging 'post-install.ps1'))) {
            throw 'the release is missing post-install.ps1'
        }

        $scoopInstallRoot = Join-Path $env:USERPROFILE '.scoop'
        New-Item -ItemType Directory -Force -Path $scoopInstallRoot | Out-Null
        # Replace distribution files so an upgrade cannot reuse an old target's slibs.
        # Keep package caches, build results and user-supplied external commands.
        foreach ($scoopComponent in 'bin', 'lib', 'include', 'src', 'vendor', 'native', 'libexec', 'docs', 'share', 'tooling') {
            $scoopPath = Join-Path $scoopInstallRoot $scoopComponent
            if (Test-Path -LiteralPath $scoopPath) { Remove-Item -LiteralPath $scoopPath -Recurse -Force }
        }
        # robocopy merges into existing directories such as commands; codes below 8 mean success.
        & robocopy.exe $scoopStaging $scoopInstallRoot /E /MOVE /NFL /NDL /NJH /NJS /NP /R:2 /W:1 | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "could not copy the toolchain into $scoopInstallRoot (robocopy exit $LASTEXITCODE)" }

        # The lib packages carry prebuilt system libraries; post-install only writes the API docs.
        # Run it in a child PowerShell so the execution policy and its exit code stay contained.
        Write-Host 'Generating API documentation...'
        $scoopPostInstall = Join-Path $scoopInstallRoot 'post-install.ps1'
        $scoopShell = (Get-Process -Id $PID).Path
        if (-not $scoopShell -or (Split-Path -Leaf $scoopShell) -notin 'powershell.exe', 'pwsh.exe') {
            $scoopShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        }
        # Windows PowerShell 5.1 -File treats "--name" arguments as parameters, so pass the
        # options inside an encoded command, quoted as PowerShell string literals.
        $scoopQuoted = @($scoopPostInstall) + $scoopPostArgs | ForEach-Object { "'" + ($_ -replace "'", "''") + "'" }
        $scoopCommand = "try { & $($scoopQuoted -join ' '); exit `$LASTEXITCODE } " +
            'catch { [Console]::Error.WriteLine("Error: $($_.Exception.Message)"); exit 1 }'
        $scoopEncoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($scoopCommand))
        & $scoopShell -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $scoopEncoded | Out-Host
        $scoopExit = $LASTEXITCODE
        if ($scoopExit -ne 0) {
            [Console]::Error.WriteLine("Installation preparation failed. Fix the reported error, then rerun:`n  & `"$scoopPostInstall`"")
            return $scoopExit
        }
        $scoopBin = Join-Path $scoopInstallRoot 'bin'
        & (Join-Path $scoopBin 'sco.exe') --version | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'the installed sco.exe does not run' }

        if (-not $NoModifyPath) { Add-ScoopUserPath $scoopBin }
        if (-not (Test-ScoopPathContains $env:Path $scoopBin)) { $env:Path = "$scoopBin;$env:Path" }
        Write-Host ''
        Write-Host "Scoop is installed in $scoopInstallRoot."
        if ($NoModifyPath) {
            Write-Host "Add $scoopBin to PATH to use it from other terminals."
        } else {
            Write-Host 'This PowerShell session can run sco now; open a new terminal elsewhere.'
        }
        Write-Host 'On Windows the driver is named sco, for example: sco run hello.scoop'
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

if ($Help) {
    Write-Host @'
Usage: install.ps1 [-Release RELEASE] [-NoModifyPath] [-- POST_INSTALL_OPTIONS...]
Install the latest Scoop release into %USERPROFILE%\.scoop.
RELEASE names a published release such as 2026-11-09 (-Version is an alias).
Examples:
  irm https://scoop-lang.org/install.ps1 | iex
  & ([scriptblock]::Create((irm https://scoop-lang.org/install.ps1))) -Release 2026-11-09 -- --jobs 2
  powershell -ExecutionPolicy Bypass -File install.ps1 -NoModifyPath
Pass post-install options with the script block form, not with -File.
'@
    return
}

# Keep execution at the end so irm | iex reads the whole script before installing.
# Report errors without exit: under irm | iex, exit would close the user's PowerShell window.
$scoopInstallExit = 1
try {
    $scoopInstallExit = Install-ScoopToolchain -Release $Release -NoModifyPath ([bool]$NoModifyPath) -PostInstallArgs $PostInstallArgs
} catch {
    [Console]::Error.WriteLine("Error: $($_.Exception.Message)")
}
if ($scoopInstallExit -ne 0 -and $PSCommandPath) { exit $scoopInstallExit }
