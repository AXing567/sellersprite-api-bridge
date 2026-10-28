#!/usr/bin/env bash
set -e

echo "============================================"
echo "  卖家精灵 API 转接桥 - Linux/macOS 启动器"
echo "============================================"

cd "$(dirname "$0")"

# ---------- 1. 检查 Python ----------
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "[错误] 未检测到 python3，请先安装 Python 3.9+"
    exit 1
fi

# ---------- 2. 检查配置 ----------
if [ ! -f config.json ]; then
    echo "[提示] 未找到 config.json，正在从模板创建..."
    cp config.example.json config.json
    echo
    echo "[!] 请编辑 config.json 填写 sellersprite.account 与 sellersprite.password 后重新运行。"
    exit 1
fi

# ---------- 3. 虚拟环境 ----------
if [ ! -d .venv ]; then
    echo "[1/3] 创建虚拟环境..."
    $PY -m venv .venv
fi

echo "[2/3] 安装依赖..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

# ---------- 4. 启动 ----------
mkdir -p data
echo "[3/3] 启动 API 服务..."
echo
echo "  接口文档: http://127.0.0.1:8000/docs"
echo "  健康检查: http://127.0.0.1:8000/health"
echo "  按 Ctrl+C 停止服务"
echo "============================================"

exec python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
