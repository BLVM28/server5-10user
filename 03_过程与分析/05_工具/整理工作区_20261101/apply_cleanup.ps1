$ErrorActionPreference = 'Stop'
$workspacePath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
$archivePath = Join-Path $workspacePath '99_归档/20261101_整理'
$plan = Get-Content -LiteralPath (Join-Path $archivePath 'cleanup_plan.json') -Raw -Encoding utf8 | ConvertFrom-Json
if ($plan.root -ne $workspacePath) { throw 'Workspace does not match approved plan' }
function Assert-InWorkspace([string] $relativePath) {
    $absolutePath = [IO.Path]::GetFullPath((Join-Path $workspacePath $relativePath))
    if (-not $absolutePath.StartsWith($workspacePath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Outside workspace: $relativePath" }
    if ($absolutePath.StartsWith((Join-Path $workspacePath '01_核心参考') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Protected references' }
    return $absolutePath
}
# Validate every deletion before mutating any file.
foreach ($entry in $plan.archived_files_to_remove) {
    $targetPath = Assert-InWorkspace $entry.path
    $item = Get-Item -LiteralPath $targetPath -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Unexpected file type: $targetPath" }
    if ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw "Changed after archiving: $targetPath" }
}
foreach ($relativePath in $plan.cache_trees_to_remove) {
    $targetPath = Assert-InWorkspace $relativePath
    $item = Get-Item -LiteralPath $targetPath -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Unexpected cache type: $targetPath" }
    $reparse = @(Get-ChildItem -LiteralPath $targetPath -Force -Recurse | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($reparse.Count -ne 0) { throw "Reparse point in cache: $targetPath" }
}
$deleted = [Collections.Generic.List[string]]::new()
foreach ($entry in $plan.archived_files_to_remove) {
    Remove-Item -LiteralPath (Assert-InWorkspace $entry.path) -Force
    $deleted.Add($entry.path)
}
foreach ($relativePath in $plan.cache_trees_to_remove) {
    Remove-Item -LiteralPath (Assert-InWorkspace $relativePath) -Recurse -Force
}
foreach ($relativePath in $plan.prune_roots) {
    $targetPath = Assert-InWorkspace $relativePath
    $dirs = Get-ChildItem -LiteralPath $targetPath -Directory -Force -Recurse | Sort-Object { $_.FullName.Length } -Descending
    foreach ($directory in $dirs) {
        if (@(Get-ChildItem -LiteralPath $directory.FullName -Force).Count -eq 0) { Remove-Item -LiteralPath $directory.FullName -Force }
    }
}
$platformDir = Assert-InWorkspace '过程与分析/01_平台资料'
New-Item -ItemType Directory -Path $platformDir -Force | Out-Null
$manualName = '2026NICT EDA平台_用户登录及使用手册_V10-副本-副本.pdf'
$manualSource = Assert-InWorkspace $manualName
$manualDestination = Assert-InWorkspace ('过程与分析/01_平台资料/' + $manualName)
if (Test-Path -LiteralPath $manualDestination) { throw 'Do not overwrite platform manual' }
$manualHash = (Get-FileHash -LiteralPath $manualSource -Algorithm SHA256).Hash
Move-Item -LiteralPath $manualSource -Destination $manualDestination
if ((Get-FileHash -LiteralPath $manualDestination -Algorithm SHA256).Hash -ne $manualHash) { throw 'Manual hash changed' }
@{archived_loose_files_removed=$deleted;cache_trees_removed=$plan.cache_trees_to_remove;manual_move=@{from=$manualName;to=('过程与分析/01_平台资料/'+$manualName);sha256=$manualHash};completed=$true} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $archivePath 'cleanup_result.json') -Encoding utf8
Write-Output "Archived loose files removed: $($deleted.Count); cache trees removed: $($plan.cache_trees_to_remove.Count); platform manual relocated with hash preserved."
