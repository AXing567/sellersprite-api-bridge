"""测试凭证统一入口。

优先级：config.json > 环境变量（SS_ACCOUNT / SS_PASSWORD）。
测试脚本一律从这里取凭证，禁止在源码里硬编码账号密码。
"""
import json
import os
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_creds():
    """返回 (account, password)，缺失时抛出可读错误。"""
    account = ""
    password = ""

    cfg = _ROOT / "config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        node = data.get("sellersprite", data)
        account = str(node.get("account", "") or "")
        password = str(node.get("password", "") or "")

    account = account or os.environ.get("SS_ACCOUNT", "")
    password = password or os.environ.get("SS_PASSWORD", "")

    if not account or not password:
        raise SystemExit(
            "缺少凭证：请先填写 config.json 的 sellersprite.account / password，"
            "或设置环境变量 SS_ACCOUNT / SS_PASSWORD。"
        )
    return account, password


if __name__ == "__main__":
    a, p = load_creds()
    print(f"account={a[:3]}****{a[-4:]}  password_len={len(p)}")
