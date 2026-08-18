@echo off
chcp 936 >nul 2>&1
setlocal

set "GAME_DIR=F:\SteamLibrary\steamapps\common\Automobilista 2"
set "TOOLS_DIR=%~dp0tools"

echo ============================================
echo   AMS2 简体中文汉化包安装
echo ============================================
echo.

if not exist "%GAME_DIR%\AMS2.exe" (
    echo [错误] 未找到 AMS2.exe: %GAME_DIR%\AMS2.exe
    echo        请修改脚本中的 GAME_DIR 变量
    pause
    exit /b 1
)

tasklist /fi "imagename eq AMS2.exe" 2>nul | find /i "AMS2.exe" >nul
if not errorlevel 1 (
    echo [错误] 游戏正在运行，请先完全退出游戏！
    pause
    exit /b 1
)
tasklist /fi "imagename eq AMS2AVX.exe" 2>nul | find /i "AMS2AVX.exe" >nul
if not errorlevel 1 (
    echo [错误] 游戏正在运行，请先完全退出游戏！
    pause
    exit /b 1
)

echo [1/3] 安装字体补丁（AMS2 + AMS2AVX，已打过自动跳过）...
python "%TOOLS_DIR%\patch_v4.py"
if errorlevel 1 goto :err
python "%TOOLS_DIR%\patch_v4_avx.py"
if errorlevel 1 goto :err
echo.

echo [2/3] 部署汉化文本...
python "%TOOLS_DIR%\deploy.py" --deploy
if errorlevel 1 goto :err
echo.

echo [3/3] 验证部署...
python "%TOOLS_DIR%\verify_deploy.py"
if errorlevel 1 echo [警告] 验证发现问题，请检查输出
echo.

echo ============================================
echo   安装完成！
echo ============================================
echo.
echo Steam 启动参数: -novr -lang Chinese-Simple
echo 如需恢复原版，运行 uninstall.bat
echo.
pause
exit /b 0

:err
echo.
echo [错误] 执行失败，请检查上方输出
pause
exit /b 1