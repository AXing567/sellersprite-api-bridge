@echo off
chcp 65001 >nul
setlocal

echo ============================================
echo   卖家精灵 API 转接桥 - Windows 启动器
echo ============================================
echo.

cd /d "%~dp0"

REM ---------- 1. 检查 Python ----------
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 python 命令，请先安装 Python 3.9+ 并加入 PATH。
    pause
    exit /b 1
)

REM ---------- 2. 检查配置 ----------
if not exist "config.json" (
    echo [提示] 未找到 config.json，正在从模板创建...
    copy /y "config.example.json" "config.json" >nul
    echo.
    echo [!] 请打开 config.json 填写 sellersprite.account 和 sellersprite.password 后重新运行本脚本。
    echo.
    pause
    exit /b 1
)

REM ---------- 3. 创建虚拟环境并安装依赖 ----------
if not exist ".venv" (
    echo [1/3] 首次运行，正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败。
        pause
        exit /b 1
    )
)

echo [2/3] 检查并安装依赖...
call .venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络或 pip 源。
    pause
    exit /b 1
)

REM ---------- 4. 启动服务 ----------
echo [3/3] 启动 API 服务...
echo.
echo   接口文档: http://127.0.0.1:8000/docs
echo   健康检查: http://127.0.0.1:8000/health
echo.
echo   按 Ctrl+C 可停止服务
echo ============================================
echo.

python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000

pause
endlocal
