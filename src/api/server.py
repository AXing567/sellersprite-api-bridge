import os
import sys
import json
import logging

# 保证项目根目录在 python path 中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import competitor, keywords, product, tracking, tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

CONFIG_PATH = os.path.join(project_root, "config.json")


def _load_server_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("server", {}) or {}
    except Exception:
        return {}


SERVER_CFG = _load_server_config()

app = FastAPI(
    title="卖家精灵 API 转接桥 (SellerSprite API Bridge)",
    description=(
        "将卖家精灵网页版会员能力转化为跨平台 REST API 服务。\n\n"
        "**架构说明**：按业务板块拆成原子接口，再在顶层做场景化聚合；"
        "内置 Cookie 持久化、拟人请求抖动与登录熔断等防封机制。\n\n"
        "**部署**：Windows 直接运行 `start.bat`；Linux/Docker 见项目内 Dockerfile。"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- 全局异常兜底 ----------------
from src.core.session_manager import SessionExpiredError


@app.exception_handler(SessionExpiredError)
async def session_expired_handler(request: Request, exc: SessionExpiredError):
    """
    会话/凭证类故障统一返回 503（服务不可用），与 429（风控限流）区分开。

    为什么区分：429 让调用方以为"等一会儿再来"，但密码错了等多久都没用；
    503 才是准确的语义——上游登录态挂了，得人去修，重试无意义。
    """
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
            "error_type": "session_expired",
            "hint": "这是登录态问题，不是限流。请检查 config.json 的账号密码，"
                    "或先在浏览器确认 sellersprite.com 能否正常登录；重试无效。",
        },
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """账号风控熔断等安全异常统一返回 429，提示不要盲目重试"""
    return JSONResponse(
        status_code=429,
        content={"detail": str(exc), "hint": "系统已触发防风控熔断，请勿在短时间内重复触发登录。"},
    )


# ---------------- 挂载各业务板块路由 ----------------
app.include_router(competitor.router)   # 板块 1: 竞品监控
app.include_router(keywords.router)     # 板块 2: 关键词挖掘与反查
app.include_router(product.router)      # 板块 3: 选产品与选市场
app.include_router(tracking.router)     # 板块 4: 常态化监控追踪
app.include_router(tools.router)        # 板块 5: 实用算法工具


@app.get("/", tags=["健康检查"], summary="服务健康检查")
def root():
    return {
        "status": "online",
        "service": "SellerSprite API Bridge",
        "version": "1.0.0",
        "docs_url": "/docs",
        "modules": [
            "competitor  竞品监控",
            "keywords    关键词挖掘与反查",
            "product     选产品与选市场",
            "tracking    常态化监控追踪",
            "tools       实用算法工具",
        ],
    }


@app.get("/health", tags=["健康检查"], summary="会话与配置状态自检")
def health():
    """
    检查配置、本地 Cookie 缓存、熔断冷却期。

    `cookie_cache_valid` 只代表**本地缓存文件里有 token**，
    不代表卖家精灵服务端仍认这个 token——真实有效性以调用业务接口的结果为准。
    """
    from src.core.session_manager import SellerSpriteSession
    try:
        mgr = SellerSpriteSession()
        has_cookie = bool(
            mgr.session.cookies.get("Sprite-X-Token") or mgr.session.cookies.get("rank-login-user")
        )
        fuse = {"tripped": False, "fail_count": 0, "last_reason": ""}
        if os.path.exists(mgr.login_state_path):
            with open(mgr.login_state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            fuse = {
                "tripped": state.get("fail_count", 0) >= mgr.max_login_retries,
                "fail_count": state.get("fail_count", 0),
                "last_reason": state.get("last_reason", ""),
            }

        # 熔断中 / 上次失败原因含凭证问题 → 明确告知"去修账号"，别让调用方以为该重试
        warning = None
        if fuse["tripped"]:
            warning = "登录熔断中，需等冷却结束；若原因是密码错误请先更正 config.json"
        elif "密码" in (fuse.get("last_reason") or ""):
            warning = "最近一次登录提示密码/账号错误，请核对 config.json"

        return {
            "status": "ok",
            "account": f"{mgr.account[:3]}****{mgr.account[-4:]}" if mgr.account else None,
            "has_cached_token": has_cookie,
            "cookie_cache_path": mgr.cookie_cache_path,
            "rate_limit": f"{mgr.min_interval}s ~ {mgr.max_interval}s",
            "login_fuse": fuse,
            "warning": warning,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


if __name__ == "__main__":
    import uvicorn
    host = SERVER_CFG.get("host", "0.0.0.0")
    port = int(SERVER_CFG.get("port", 8000))
    uvicorn.run("src.api.server:app", host=host, port=port, reload=False)
