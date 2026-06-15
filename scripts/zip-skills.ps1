# Package skills as .zip for Claude Desktop
# Usage: .\zip-skills.ps1              (all skills)
#        .\zip-skills.ps1 docs-doc-patcher   (one skill)

param([string]$SkillName = "")

$Root = Split-Path $PSScriptRoot -Parent
$Dist = Join-Path $Root "dist"
$Exclude = @("research", "test-inputs", "EVAL.md", "PROGRAM.md", "SCOPE.md", "__pycache__")

New-Item -ItemType Directory -Force -Path $Dist | Out-Null

$count = 0
Get-ChildItem -Path (Join-Path $Root "src") -Filter "SKILL.md" -Recurse | ForEach-Object {
    $dir = $_.DirectoryName
    $name = Split-Path $dir -Leaf

    if ($SkillName -and $name -ne $SkillName) { return }

    $zipPath = Join-Path $Dist "$name.zip"
    if (Test-Path $zipPath) { Remove-Item $zipPath }

    $tempDir = Join-Path $env:TEMP "skill-zip-$name"
    if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse }

    # Copy skill dir, excluding non-execution files
    Copy-Item $dir $tempDir -Recurse
    foreach ($ex in $Exclude) {
        Get-ChildItem -Path $tempDir -Filter $ex -Recurse -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    # Remove brainstorm/memo files
    Get-ChildItem -Path $tempDir -Filter ".brainstorm-*" -Force -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $tempDir -Filter ".decision-memo-*" -Force -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue

    Compress-Archive -Path (Join-Path $tempDir "*") -DestinationPath $zipPath
    Remove-Item $tempDir -Recurse

    Write-Host "  zip   $name -> dist\$name.zip"
    $script:count++
}

Write-Host ""
Write-Host "Packaged $count skill(s) -> $Dist"
