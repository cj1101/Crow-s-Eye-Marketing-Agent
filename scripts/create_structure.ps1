# Create new directory structure for Crow's Eye Marketing Platform

$directories = @(
    "src\components\media",
    "src\components\forms", 
    "src\components\dialogs",
    "src\components\common",
    "src\features",
    "src\features\gallery",
    "src\features\scheduling", 
    "src\features\posting",
    "src\features\authentication",
    "src\features\media_processing",
    "src\api",
    "src\api\meta",
    "src\api\twitter", 
    "src\api\linkedin",
    "src\api\ai",
    "assets",
    "assets\icons",
    "assets\styles",
    "assets\images", 
    "tests",
    "tests\unit",
    "tests\integration",
    "tests\fixtures",
    "scripts",
    "data",
    "data\templates",
    "data\samples",
    "deployment"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created: $dir"
    } else {
        Write-Host "Exists: $dir"
    }
}

Write-Host "Directory structure creation complete!" 