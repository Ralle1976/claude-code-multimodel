<#
.SYNOPSIS
    Automates the setup and connection to a DevContainer environment using either Docker or Podman on Windows.

.DESCRIPTION
    This script automates the process of initializing, starting, and connecting to a DevContainer
    using either Docker or Podman as the container backend. It must be executed from the root
    directory of your project and assumes the script is located in a 'Script' subdirectory.

    Native commands (docker/podman/devcontainer) do not throw on a non-zero exit code in
    PowerShell, so every call is checked explicitly via $LASTEXITCODE.

.PARAMETER Backend
    Specifies the container backend to use. Valid values are 'docker' or 'podman'.

.EXAMPLE
    .\Script\run_devcontainer_claude_code.ps1 -Backend docker
    Uses Docker as the container backend.

.EXAMPLE
    .\Script\run_devcontainer_claude_code.ps1 -Backend podman
    Uses Podman as the container backend.

.NOTES
    Project Structure:
    Project/
    ├── .devcontainer/
    └── Script/
        └── run_devcontainer_claude_code.ps1
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('docker','podman')]
    [string]$Backend
)

# Notify script start
Write-Host "--- DevContainer Startup & Connection Script ---"
Write-Host "Using backend: $($Backend)"

# Exit code of the most recent Invoke-Native call.
$script:LastNativeExitCode = 0

function Invoke-Native {
    <#
        Runs a native command, keeps its output visible and records the exit
        code in $script:LastNativeExitCode.

        Unlike cmdlets, native executables never raise a terminating error in
        PowerShell - the exit code has to be inspected manually. The function
        deliberately returns nothing so command output stays on the pipeline.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Arguments = @(),
        [switch]$AllowFailure
    )

    & $Command @Arguments
    $script:LastNativeExitCode = $LASTEXITCODE

    if ($script:LastNativeExitCode -ne 0 -and -not $AllowFailure) {
        throw "Command '$Command $($Arguments -join ' ')' failed with exit code $script:LastNativeExitCode."
    }
}

function Invoke-NativeQuiet {
    <# Same as Invoke-Native, but suppresses all command output. #>
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Arguments = @(),
        [switch]$AllowFailure
    )

    & $Command @Arguments *> $null
    $script:LastNativeExitCode = $LASTEXITCODE

    if ($script:LastNativeExitCode -ne 0 -and -not $AllowFailure) {
        throw "Command '$Command $($Arguments -join ' ')' failed with exit code $script:LastNativeExitCode."
    }
}

# --- Prerequisite Check ---
Write-Host "Checking for required commands..."
try {
    if (-not (Get-Command $Backend -ErrorAction SilentlyContinue)) {
        throw "Required command '$($Backend)' not found."
    }
    Write-Host "- $($Backend) command found."
    if (-not (Get-Command devcontainer -ErrorAction SilentlyContinue)) {
        throw "Required command 'devcontainer' not found."
    }
    Write-Host "- devcontainer command found."
}
catch {
    Write-Error "A required command is not installed or not in your PATH. $($_.Exception.Message)"
    Write-Error "Please ensure both '$Backend' and 'devcontainer' are installed and accessible in your system's PATH."
    exit 1
}


# --- Backend-Specific Initialization ---
if ($Backend -eq 'podman') {
    Write-Host "--- Podman Backend Initialization ---"

    # --- Step 1a: Initialize Podman machine ---
    Write-Host "Initializing Podman machine 'claudeVM'..."
    try {
        # An already existing machine makes 'init' fail; that is not fatal here.
        Invoke-Native -Command 'podman' -Arguments @('machine', 'init', 'claudeVM') -AllowFailure
        if ($script:LastNativeExitCode -ne 0) {
            Write-Warning "Podman machine 'claudeVM' could not be created (exit code $script:LastNativeExitCode) - it may already exist."
        } else {
            Write-Host "Podman machine 'claudeVM' initialized."
        }
    } catch {
        Write-Error "Failed to initialize Podman machine: $($_.Exception.Message)"
        exit 1 # Exit script on error
    }

    # --- Step 1b: Start Podman machine ---
    Write-Host "Starting Podman machine 'claudeVM'..."
    try {
        Invoke-NativeQuiet -Command 'podman' -Arguments @('machine', 'start', 'claudeVM', '-q')
        Write-Host "Podman machine started or already running."
    } catch {
        Write-Error "Failed to start Podman machine: $($_.Exception.Message)"
        exit 1
    }

    # --- Step 2: Set default connection ---
    Write-Host "Setting default Podman connection to 'claudeVM'..."
    try {
        Invoke-NativeQuiet -Command 'podman' -Arguments @('system', 'connection', 'default', 'claudeVM') -AllowFailure
        if ($script:LastNativeExitCode -eq 0) {
            Write-Host "Default connection set."
        } else {
            Write-Warning "Failed to set default Podman connection (exit code $script:LastNativeExitCode) - may be already set or machine issue."
        }
    } catch {
        Write-Warning "Failed to set default Podman connection: $($_.Exception.Message)"
    }

} elseif ($Backend -eq 'docker') {
    Write-Host "--- Docker Backend Initialization ---"

    # --- Step 1 & 2: Check Docker Desktop ---
    Write-Host "Checking if Docker Desktop is running and docker command is available..."
    try {
        Invoke-NativeQuiet -Command 'docker' -Arguments @('info')
        Write-Host "Docker Desktop (daemon) is running."
    } catch {
        Write-Error "Docker Desktop is not running or docker command not found."
        Write-Error "Please ensure Docker Desktop is running."
        exit 1
    }
}

# --- Step 3: Bring up DevContainer ---
Write-Host "Bringing up DevContainer in the current folder..."
try {
    $arguments = @('up', '--workspace-folder', '.')
    if ($Backend -eq 'podman') {
        $arguments += '--docker-path', 'podman'
    }
    Invoke-Native -Command 'devcontainer' -Arguments $arguments
    Write-Host "DevContainer startup process completed."
} catch {
    Write-Error "Failed to bring up DevContainer: $($_.Exception.Message)"
    exit 1
}

# --- Step 4: Get DevContainer ID ---
Write-Host "Finding the DevContainer ID..."
$currentFolder = (Get-Location).Path

try {
    # Several containers can match; take the first non-empty line. Calling
    # .Trim() on the raw pipeline output fails when it is an array.
    $rawId = & $Backend ps --filter "label=devcontainer.local_folder=$currentFolder" --format '{{.ID}}'
    $psExit = $LASTEXITCODE
    if ($psExit -ne 0) {
        throw "Command '$Backend ps' failed with exit code $psExit."
    }

    $containerId = @($rawId) |
        Where-Object { $_ -and "$_".Trim() } |
        ForEach-Object { "$_".Trim() } |
        Select-Object -First 1
} catch {
    $displayCommand = "$Backend ps --filter `"label=devcontainer.local_folder=$currentFolder`" --format '{{.ID}}'"
    Write-Error "Failed to get container ID (Command: $displayCommand): $($_.Exception.Message)"
    exit 1
}

if (-not $containerId) {
    Write-Error "Could not find DevContainer ID for the current folder ('$currentFolder')."
    Write-Error "Please check if 'devcontainer up' was successful and the container is running."
    exit 1
}
Write-Host "Found container ID: $containerId"

# --- Step 5 & 6: Execute command and enter interactive shell inside container ---
Write-Host "Executing 'claude' command and then starting zsh session inside container $($containerId)..."
try {
    & $Backend exec -it $containerId zsh -c 'claude; exec zsh'
    $execExit = $LASTEXITCODE
    Write-Host "Interactive session ended (exit code $execExit)."
    if ($execExit -ne 0) {
        Write-Warning "The interactive session returned exit code $execExit."
    }
} catch {
    $displayCommand = "$Backend exec -it $containerId zsh -c 'claude; exec zsh'"
    Write-Error "Failed to execute command inside container (Command: $displayCommand): $($_.Exception.Message)"
    exit 1
}

# Notify script completion
Write-Host "--- Script completed ---"
