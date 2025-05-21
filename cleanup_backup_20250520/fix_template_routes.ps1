# Script to fix all URL route issues in templates
Write-Host "Scanning all HTML templates for URL route issues..." -ForegroundColor Cyan

# Get all HTML files
$htmlFiles = Get-ChildItem -Path ".\backend\templates" -Recurse -Filter "*.html"

foreach ($file in $htmlFiles) {
    Write-Host "Checking $($file.FullName)..." -ForegroundColor Yellow
    
    # Read the file content
    $content = Get-Content -Path $file.FullName -Raw
    
    # Replace incorrect URL routes
    if ($content -match "url_for\('index'\)") {
        Write-Host "  - Found incorrect 'index' route, fixing..." -ForegroundColor Red
        $content = $content -replace "url_for\('index'\)", "url_for('main.index')"
        Set-Content -Path $file.FullName -Value $content
    }
}

Write-Host "Template scan and fixes completed!" -ForegroundColor Green
