# setup.ps1 - Codex Elixir Phoenix Installation Script
# This script injects the .codex framework into a target Phoenix project.

param (
    [Parameter(Mandatory=$true, Position=0, HelpMessage="The path to your Phoenix project root.")]
    [string]$TargetPath
)

$SourceDir = ".codex"

# --- Validation ---
if (-not (Test-Path $TargetPath -PathType Container)) {
    Write-Host "Error: Target directory '$TargetPath' does not exist." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $SourceDir -PathType Container)) {
    Write-Host "Error: Source directory '$SourceDir' not found. Please run this script from the root of the codex-elixir-phoenix distribution." -ForegroundColor Red
    exit 1
}

$TargetAbsPath = [System.IO.Path]::GetFullPath($TargetPath)

Write-Host "🚀 Injecting Codex framework into: $TargetAbsPath" -ForegroundColor Cyan

# --- Implementation ---
# Copy .codex directory to target
# Copy-Item is used. Recurse handles subdirectories.
# Force ensures it can overwrite if it exists (standard setup behavior).
try {
    Copy-Item -Path $SourceDir -Destination "$TargetAbsPath\" -Recurse -Force -ErrorAction Stop
    Write-Host "✅ Codex successfully injected into: $TargetAbsPath" -ForegroundColor Green
    Write-Host "💡 To begin, run: cd `"$TargetPath`"; codex `$phx-intro" -ForegroundColor Yellow
} catch {
    Write-Host "An error occurred while copying the framework: $_" -ForegroundColor Red
    exit 1
}
