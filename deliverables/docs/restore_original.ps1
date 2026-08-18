# 一键还原官方原版 AMS2.exe / AMS2AVX.exe（使用补丁脚本生成的原版备份）
$ErrorActionPreference = 'Stop'
$gameDir = 'F:\SteamLibrary\steamapps\common\Automobilista 2'

if (Get-Process | Where-Object { $_.ProcessName -match 'AMS2' }) {
    Write-Host '[错误] 游戏正在运行，请先完全退出游戏。' -ForegroundColor Red
    exit 1
}
foreach ($exe in 'AMS2.exe', 'AMS2AVX.exe') {
    $bak = Join-Path $gameDir "$exe.bak-v4-orig"
    if (Test-Path $bak) {
        Copy-Item $bak (Join-Path $gameDir $exe) -Force
        Write-Host "已还原 $exe"
    } else {
        Write-Host "[警告] 未找到 $bak ，可用 Steam '验证游戏文件完整性' 还原。" -ForegroundColor Yellow
    }
}
