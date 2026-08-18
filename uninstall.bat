@echo off
chcp 65001 >nul 2>&1
setlocal

set "GAME_DIR=F:\SteamLibrary\steamapps\common\Automobilista 2"
set "PROJ_DIR=%~dp0"

echo ============================================
echo   AMS2 汉化包卸载（恢复原版）
echo ============================================
echo.

set "restored=0"

rem --- 1. 恢复两个 exe（V4 补丁原版备份）---
if exist "%GAME_DIR%\AMS2.exe.bak-v4-orig" (
    copy /y "%GAME_DIR%\AMS2.exe.bak-v4-orig" "%GAME_DIR%\AMS2.exe" >nul
    echo [OK] 已恢复 AMS2.exe
    set "restored=1"
) else (
    echo [跳过] 未找到 AMS2.exe.bak-v4-orig（可用 Steam 验证文件完整性还原）
)
if exist "%GAME_DIR%\AMS2AVX.exe.bak-v4-orig" (
    copy /y "%GAME_DIR%\AMS2AVX.exe.bak-v4-orig" "%GAME_DIR%\AMS2AVX.exe" >nul
    echo [OK] 已恢复 AMS2AVX.exe
    set "restored=1"
) else (
    echo [跳过] 未找到 AMS2AVX.exe.bak-v4-orig
)

rem --- 2. 恢复 BOOTFLOW.bff（汉化文本）---
if exist "%GAME_DIR%\Pakfiles\BOOTFLOW.bff.bak" (
    copy /y "%GAME_DIR%\Pakfiles\BOOTFLOW.bff.bak" "%GAME_DIR%\Pakfiles\BOOTFLOW.bff" >nul
    echo [OK] 已恢复 BOOTFLOW.bff（游戏目录备份）
    set "restored=1"
) else if exist "%PROJ_DIR%work\deploy\backup\BOOTFLOW.bff.bak" (
    copy /y "%PROJ_DIR%work\deploy\backup\BOOTFLOW.bff.bak" "%GAME_DIR%\Pakfiles\BOOTFLOW.bff" >nul
    echo [OK] 已恢复 BOOTFLOW.bff（工程备份）
    set "restored=1"
) else (
    echo [跳过] 未找到 BOOTFLOW.bff 备份（可用 Steam 验证文件完整性还原）
)

echo.
if "%restored%"=="1" (
    echo ============================================
    echo   卸载完成！游戏已恢复原版
    echo ============================================
) else (
    echo [警告] 未找到任何备份文件，请用 Steam 验证文件完整性还原
)
echo.
pause
