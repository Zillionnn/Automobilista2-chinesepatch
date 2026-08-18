# 一键应用 AMS2 简中渲染补丁（需先完全退出游戏）
$ErrorActionPreference = 'Stop'
$gameDir = 'F:\SteamLibrary\steamapps\common\Automobilista 2'

if (Get-Process | Where-Object { $_.ProcessName -match 'AMS2' }) {
    Write-Host '[错误] 游戏正在运行，请先完全退出游戏再应用补丁。' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $gameDir)) {
    Write-Host "[错误] 未找到游戏目录: $gameDir" -ForegroundColor Red
    exit 1
}

Write-Host '[1/2] 打 AMS2.exe（非 AVX）...' -ForegroundColor Cyan
python (Join-Path $PSScriptRoot '..\patch\patch_v4.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '[2/2] 打 AMS2AVX.exe ...' -ForegroundColor Cyan
python (Join-Path $PSScriptRoot '..\patch\patch_v4_avx.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '完成！请通过 Steam 启动游戏验证中文显示。' -ForegroundColor Green
