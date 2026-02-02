# Maxwell Installation Script for Windows PowerShell
# Usage: iwr -useb https://raw.githubusercontent.com/your-repo/maxwell/main/scripts/install.ps1 | iex

$ErrorActionPreference = "Stop"

# Colors
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Blue }
function Write-Success { Write-Host "[SUCCESS] $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red; exit 1 }

# ASCII Art Banner
function Show-Banner {
    Write-Host ""
    Write-Host "  __  __                        _ _ " -ForegroundColor Blue
    Write-Host " |  \/  | __ ___  ____      _____| | |" -ForegroundColor Blue
    Write-Host " | |\/| |/ _`` \ \/ /\ \ /\ / / _ \ | |" -ForegroundColor Blue
    Write-Host " | |  | | (_| |>  <  \ V  V /  __/ | |" -ForegroundColor Blue
    Write-Host " |_|  |_|\__,_/_/\_\  \_/\_/ \___|_|_|" -ForegroundColor Blue
    Write-Host ""
    Write-Host " Local-First Fiction Writing IDE" -ForegroundColor Blue
    Write-Host ""
}

# Check if command exists
function Test-Command {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check Docker
    if (-not (Test-Command "docker")) {
        Write-Error "Docker is not installed. Please install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/"
    }

    # Check if Docker is running
    try {
        docker info 2>$null | Out-Null
    }
    catch {
        Write-Error "Docker is not running. Please start Docker Desktop and try again."
    }

    Write-Success "All prerequisites met!"
}

# Get installation directory
function Get-InstallDirectory {
    $defaultDir = Join-Path $env:USERPROFILE "maxwell"

    Write-Host ""
    $userInput = Read-Host "Installation directory [$defaultDir]"

    if ([string]::IsNullOrWhiteSpace($userInput)) {
        return $defaultDir
    }

    return $userInput
}

# Download Maxwell
function Get-Maxwell {
    param($Directory)

    Write-Info "Downloading Maxwell to $Directory..."

    if (Test-Path $Directory) {
        Write-Warn "Directory $Directory already exists."
        $update = Read-Host "Do you want to update it? [y/N]"

        if ($update -eq "y" -or $update -eq "Y") {
            Set-Location $Directory
            if (Test-Path ".git") {
                git pull origin main
            }
            else {
                Write-Error "Cannot update: not a git repository. Please remove the directory and try again."
            }
        }
        else {
            Write-Info "Using existing installation."
        }
    }
    else {
        if (Test-Command "git") {
            git clone https://github.com/your-repo/maxwell.git $Directory
        }
        else {
            Write-Warn "Git not found, downloading as zip..."
            New-Item -ItemType Directory -Force -Path $Directory | Out-Null
            $zipPath = Join-Path $env:TEMP "maxwell.zip"
            Invoke-WebRequest -Uri "https://github.com/your-repo/maxwell/archive/main.zip" -OutFile $zipPath
            Expand-Archive -Path $zipPath -DestinationPath $env:TEMP -Force
            Copy-Item -Path (Join-Path $env:TEMP "maxwell-main\*") -Destination $Directory -Recurse
            Remove-Item -Path $zipPath -Force
            Remove-Item -Path (Join-Path $env:TEMP "maxwell-main") -Recurse -Force
        }
    }

    Write-Success "Maxwell downloaded successfully!"
}

# Start Maxwell
function Start-Maxwell {
    param($Directory)

    Write-Info "Building and starting Maxwell..."
    Set-Location $Directory

    # Use docker compose
    docker compose up -d --build

    Write-Success "Maxwell is starting..."
}

# Wait for services
function Wait-ForReady {
    Write-Info "Waiting for services to be ready..."

    $maxAttempts = 30
    $attempt = 1

    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "Maxwell is ready!"
                return
            }
        }
        catch {
            # Service not ready yet
        }

        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
        $attempt++
    }

    Write-Host ""
    Write-Warn "Maxwell may still be starting. Check with: docker-compose logs -f"
}

# Show success message
function Show-Success {
    param($Directory)

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Maxwell installed successfully!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Open Maxwell: http://localhost:3000"
    Write-Host ""
    Write-Host "  Useful commands:"
    Write-Host "    cd $Directory"
    Write-Host "    docker-compose logs -f     # View logs"
    Write-Host "    docker-compose stop        # Stop Maxwell"
    Write-Host "    docker-compose start       # Start Maxwell"
    Write-Host "    docker-compose down        # Stop and remove containers"
    Write-Host ""
    Write-Host "  Your data is stored in a Docker volume and persists"
    Write-Host "  across restarts. To backup your data:"
    Write-Host "    docker cp maxwell_backend:/app/data .\maxwell-backup"
    Write-Host ""
    Write-Host "Happy writing!" -ForegroundColor Blue
    Write-Host ""
}

# Main function
function Install-Maxwell {
    Show-Banner

    Write-Host "This script will install Maxwell on your system using Docker."
    Write-Host "All your writing data will be stored locally on your machine."
    Write-Host ""

    Test-Prerequisites

    $installDir = Get-InstallDirectory

    Get-Maxwell -Directory $installDir
    Start-Maxwell -Directory $installDir
    Wait-ForReady
    Show-Success -Directory $installDir

    # Open browser
    Start-Process "http://localhost:3000"
}

# Run installation
Install-Maxwell
