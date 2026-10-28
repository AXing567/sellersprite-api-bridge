import os
import re
import json
import time
import random
import logging
import hashlib
import threading
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)


class SessionExpiredError(RuntimeError):
    """会话失效且无法自动恢复（账号密码错误 / 熔断中 / 风控拦截）"""


class SellerSpriteSession:
    """
    卖家精灵工业级会话与账号安全防护引擎：
    1. 【严格 Cookie 本地持久化缓存】：一次登录，持久复用 7 天（168 小时），绝不重复调用登录接口。
    2. 【登录熔断与频率限制】：24 小时内最多允许登录失败 3 次；触发失败后进入 30 分钟冷却期，拒绝连续冲击登录接口。
    3. 【智能抖动延时 (Human-Jitter)】：每次对卖家精灵业务接口的请求之间强制插入 2.0 ~ 4.0 秒的拟人随机停顿。
    4. 【多线程并发防重锁】：使用线程安全锁，避免并发请求时重复发起登录请求。
    5. 【异常静默熔断保护】：如果检测到“账号已锁定”或“验证码”特征，立刻停机告警，绝不盲目重试。
    """

    LOGIN_PAGE_URL = "https://www.sellersprite.com/cn/w/user/login"
    SIGNIN_URL = "https://www.sellersprite.com/w/user/signin"
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def __init__(self, config_path: Optional[str] = None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.config_path = config_path or os.path.join(self.base_dir, "config.json")
        self.data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.account: str = ""
        self.password: str = ""
        self.default_marketplace: str = "US"
        self.user_agent: str = self.DEFAULT_UA

        # 安全防封策略配置
        self.cookie_cache_path = os.path.join(self.data_dir, "session_cookies.json")
        self.login_state_path = os.path.join(self.data_dir, "login_guard.json")
        self.cookie_ttl_hours: int = 168
        self.min_interval: float = 2.0
        self.max_interval: float = 4.0
        self.max_login_retries: int = 3
        self.login_cooldown_minutes: int = 30
        self.enable_jitter: bool = True

        self._last_request_time: float = 0.0
        self._lock = threading.RLock()

        self.session = requests.Session()
        self._load_config()
        self._init_session_headers()
        self._try_load_cached_cookies()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            ss_cfg = cfg.get("sellersprite", {})
            sec_cfg = cfg.get("security", {})

            self.account = ss_cfg.get("account", "").strip()
            self.password = ss_cfg.get("password", "").strip()
            self.default_marketplace = ss_cfg.get("default_marketplace", "US")
            self.user_agent = ss_cfg.get("user_agent", self.DEFAULT_UA)

            if sec_cfg.get("cookie_cache_path"):
                self.cookie_cache_path = os.path.join(self.base_dir, sec_cfg.get("cookie_cache_path"))
            self.cookie_ttl_hours = sec_cfg.get("cookie_ttl_hours", 168)
            self.min_interval = sec_cfg.get("min_request_interval_seconds", 2.0)
            self.max_interval = sec_cfg.get("max_request_interval_seconds", 4.0)
            self.max_login_retries = sec_cfg.get("max_login_retries_per_day", 3)
            self.login_cooldown_minutes = sec_cfg.get("login_cooldown_minutes", 30)
            self.enable_jitter = sec_cfg.get("enable_request_jitter", True)

    def _init_session_headers(self):
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": self.LOGIN_PAGE_URL,
            "Origin": "https://www.sellersprite.com"
        })

    def _wait_for_rate_limit(self):
        """规则 1：拟人请求频率限制与随机微抖动"""
        if not self.enable_jitter:
            return

        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            jitter = random.uniform(self.min_interval, self.max_interval)
            if elapsed < jitter:
                sleep_time = jitter - elapsed
                logger.debug(f"[防风控保护] 拟人延迟等待: {sleep_time:.2f} 秒")
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    def _try_load_cached_cookies(self) -> bool:
        """规则 2：优先读取本地缓存的 Cookie，避免重复登录"""
        if not os.path.exists(self.cookie_cache_path):
            return False

        try:
            with open(self.cookie_cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            saved_time = data.get("saved_at", 0)
            cookies_dict = data.get("cookies", {})
            saved_account = data.get("account", "")

            # 校验账号与有效期（TTL 默认 7 天）
            if saved_account != self.account:
                logger.info("[会话管理器] 账号已变更，放弃旧 Cookie 缓存")
                return False

            if time.time() - saved_time > self.cookie_ttl_hours * 3600:
                logger.info("[会话管理器] 本地 Cookie 缓存已超期，需要重新换取")
                return False

            if not cookies_dict:
                return False

            self.session.cookies.update(cookies_dict)
            logger.info(f"[会话管理器] 成功载入本地 Cookie 缓存（保留自: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(saved_time))}）")
            return True
        except Exception as e:
            logger.warning(f"[会话管理器] 读取本地 Cookie 缓存失败: {e}")
            return False

    def _save_cookies_to_cache(self):
        """持久化保存当前 Session 的 Cookie"""
        try:
            data = {
                "account": self.account,
                "saved_at": time.time(),
                "cookies": self.session.cookies.get_dict()
            }
            with open(self.cookie_cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"[会话管理器] 登录凭证已固化到本地: {self.cookie_cache_path}")
        except Exception as e:
            logger.error(f"[会话管理器] 固化本地 Cookie 失败: {e}")

    def _check_login_fuse(self) -> bool:
        """规则 3：登录熔断检查，防止连续重试导致被封号"""
        if not os.path.exists(self.login_state_path):
            return True

        try:
            with open(self.login_state_path, "r", encoding="utf-8") as f:
                state = json.load(f)

            fail_count = state.get("fail_count", 0)
            last_fail_time = state.get("last_fail_time", 0)
            cooldown_seconds = self.login_cooldown_minutes * 60

            # 超过 24 小时自动重置计数
            if time.time() - last_fail_time > 86400:
                self._record_login_result(success=True)
                return True

            if fail_count >= self.max_login_retries:
                remaining = int(cooldown_seconds - (time.time() - last_fail_time))
                if remaining > 0:
                    error_msg = f"[防风控熔断触发] 24小时内登录失败达 {fail_count} 次，为保护账号安全，处于强制冷静期！剩余解锁时间: {remaining} 秒"
                    logger.critical(error_msg)
                    raise RuntimeError(error_msg)
                else:
                    # 冷却结束，允许一次谨慎尝试
                    logger.info("[防风控熔断] 冷却时间已过，放行一次重试")
                    return True
            return True
        except RuntimeError:
            raise
        except Exception as e:
            logger.warning(f"读取熔断状态文件出错: {e}")
            return True

    def _record_login_result(self, success: bool, reason: str = ""):
        """记录登录成败状态与熔断计数器"""
        try:
            state = {
                "fail_count": 0 if success else 1,
                "last_fail_time": 0 if success else time.time(),
                "last_success_time": time.time() if success else 0,
                "last_reason": reason
            }
            if not success and os.path.exists(self.login_state_path):
                with open(self.login_state_path, "r", encoding="utf-8") as f:
                    old = json.load(f)
                    # 24 小时内累计
                    if time.time() - old.get("last_fail_time", 0) < 86400:
                        state["fail_count"] = old.get("fail_count", 0) + 1

            with open(self.login_state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"记录登录状态失败: {e}")

    def _extract_login_error(self, html: str) -> str:
        """精确提取登录页原生错误提示（只读 #login_error_message 元素）"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            node = soup.find(id="login_error_message")
            if node:
                txt = node.get_text(strip=True)
                if txt:
                    return txt
        except Exception:
            pass
        return ""

    @staticmethod
    def is_login_html(html: str) -> bool:
        """
        判断返回的 HTML 是否为「登录页」。

        为什么必须有这个函数：卖家精灵在会话失效时**不一定返回 302**，
        而是直接 HTTP 200 返回登录页（约 62KB）。如果只看状态码，
        业务层会把「未登录」误判成「没有数据 / 没有会员额度」，
        对外表现为"接口坏了"，排查成本极高。
        """
        if not html:
            return False
        m = _TITLE_RE.search(html)
        title = (m.group(1) or "").strip() if m else ""
        if "登录" in title and ("卖家精灵" in title or "SellerSprite" in title):
            return True
        if 'action="/w/user/signin"' in html and 'id="login_error_message"' in html:
            return True
        return False

    def _resp_is_login_page(self, resp: requests.Response) -> bool:
        """仅对 HTML 且体积像登录页（<200KB）的响应做判定，避免误伤大页面"""
        try:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "html" not in ctype:
                return False
            text = resp.text or ""
            if len(text) > 200_000:
                return False
            return self.is_login_html(text)
        except Exception:
            return False

    def login(self, force: bool = False) -> bool:
        """
        受严格安全防护的登录动作：
        - 非 force 模式下，有本地可用 Cookie 则绝不重复调登录接口
        - 触发熔断保护时直接抛错中断，杜绝短时间撞库
        - 校验风控特征字符串，发现异常立刻停机告警
        """
        with self._lock:
            # 1. 尝试缓存
            if not force and self._try_load_cached_cookies():
                logger.info("[会话管理器] 本地已有可用凭证，跳过模拟登录步骤")
                return True

            # 2. 熔断检查
            self._check_login_fuse()

            if not self.account or not self.password or self.password == "REDACTED":
                raise ValueError("请在 config.json 中配置有效的 account 和 password")

            logger.warning(f"[会话管理器] 准备发起向卖家精灵的安全登录请求 (账号: {self.account[:3]}****{self.account[-4:]})")
            self._wait_for_rate_limit()

            recorded = False  # 防止同一轮失败被 _record_login_result 计两次（会加速触发熔断）
            try:
                # 访问登录前导页
                self.session.get(self.LOGIN_PAGE_URL, timeout=15)
                self._wait_for_rate_limit()

                # 密码 MD5
                pwd_md5 = hashlib.md5(self.password.encode("utf-8")).hexdigest()
                payload = {
                    "email": self.account,
                    "password": pwd_md5,
                    "autoLogin": "Y",
                    "callback": ""
                }

                resp = self.session.post(self.SIGNIN_URL, data=payload, allow_redirects=True, timeout=15)

                # 保存诊断副本（便于离线分析，避免反复登录）
                try:
                    debug_dir = os.path.join(self.data_dir, "debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    with open(os.path.join(debug_dir, "last_signin.html"), "w", encoding="utf-8") as df:
                        df.write(resp.text)
                except Exception:
                    pass

                # 精确解析登录页原生错误提示（#login_error_message）
                err_msg = self._extract_login_error(resp.text)
                if err_msg:
                    self._record_login_result(success=False, reason=err_msg)
                    recorded = True

                    # ★ 密码/账号错误：这是凭证问题，绝不能重试，否则 10 次就把账号锁死
                    if "密码错误" in err_msg or "账号或密码" in err_msg or "用户不存在" in err_msg:
                        raise SessionExpiredError(
                            f"【凭证失效】{err_msg} —— "
                            "请核对 config.json 里的 account / password 是否仍然有效"
                            "（账号可能已改密码）。已立即停止重试，避免连续错误导致账号被锁定。"
                        )
                    if "锁定" in err_msg:
                        raise SessionExpiredError(
                            f"【卖家精灵风控拦截】{err_msg} —— 请在网页端重置密码解锁后重试。系统已自动熔断，不再重试。"
                        )
                    if "验证码" in err_msg or "过于频繁" in err_msg:
                        raise SessionExpiredError(
                            f"【卖家精灵风控拦截】{err_msg} —— 已暂停自动登录，请稍后人工确认。"
                        )
                    logger.error(f"登录被拒: {err_msg}")
                    return False

                cookies = self.session.cookies.get_dict()
                token = cookies.get("Sprite-X-Token") or cookies.get("rank-login-user")

                if token or (resp.status_code == 200 and "w/user/login" not in resp.url and "退出" in resp.text):
                    logger.info("🎉 卖家精灵会话登录成功！凭证已获取。")
                    self._save_cookies_to_cache()
                    self._record_login_result(success=True)
                    return True
                else:
                    self._record_login_result(success=False, reason=f"未获取到token, status={resp.status_code}")
                    recorded = True
                    logger.error(f"登录未能提取到有效凭证，响应URL: {resp.url}")
                    return False

            except Exception as e:
                if not recorded:
                    self._record_login_result(success=False, reason=str(e))
                logger.error(f"登录过程发生异常: {e}")
                raise

    def get_session(self) -> requests.Session:
        """
        获取带凭据的请求 Session，优先复用本地 Cookie
        """
        token = self.session.cookies.get("Sprite-X-Token") or self.session.cookies.get("rank-login-user")
        if not token:
            # 优先尝试从本地文件恢复
            if not self._try_load_cached_cookies():
                self.login()
        return self.session

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        统一受控请求入口：内置防风控延时、自动保活检测、登录页拦截。

        关键设计：会话失效时**优先抛 SessionExpiredError**，
        绝不把登录页 HTML 当业务数据返回给上层解析器——
        否则上层会误报成「没有数据 / 没有会员额度」，把"没登录"伪装成"没权限"。
        """
        self._wait_for_rate_limit()
        session = self.get_session()

        # 增加通用头
        headers = kwargs.get("headers", {})
        token = self.session.cookies.get("Sprite-X-Token") or self.session.cookies.get("rank-login-user")
        if token and "Sprite-X-Token" not in headers:
            headers["Sprite-X-Token"] = token
        kwargs["headers"] = headers

        resp = session.request(method, url, **kwargs)

        # 掉线判定三条件：302 跳转 / 明确过期码 / HTTP 200 但内容是登录页
        expired = (
            resp.status_code == 302
            or "ERR_GLOBAL_SESSION_EXPIRED" in (resp.text or "")
            or self._resp_is_login_page(resp)
        )

        if expired:
            logger.warning("检测到会话失效，准备重新载入...")
            # 清除失效的本地 Cookie，强制重登一次
            if os.path.exists(self.cookie_cache_path):
                try:
                    os.remove(self.cookie_cache_path)
                except Exception:
                    pass
            try:
                self.login(force=True)
            except SessionExpiredError as e:
                raise SessionExpiredError(
                    f"{e} —— 当前所有依赖登录的接口都不可用，请先修复账号凭证。"
                ) from e

            self._wait_for_rate_limit()
            resp = self.get_session().request(method, url, **kwargs)

            # 重登后仍然是登录页 → 不再硬扛，直接报错
            if self._resp_is_login_page(resp):
                raise SessionExpiredError(
                    "会话已失效且自动重登未能恢复（仍返回登录页）。"
                    "常见原因：账号在别处被踢下线、密码已变更、或套餐到期。"
                    "请先在浏览器打开 sellersprite.com 手动确认能否登录。"
                )

        return resp
