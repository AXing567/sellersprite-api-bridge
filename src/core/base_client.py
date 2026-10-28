import logging
import requests
from typing import Optional, Dict, Any
from src.core.session_manager import SellerSpriteSession

logger = logging.getLogger(__name__)

class BaseClient:
    """
    底层受控请求客户端基类：
    所有业务模块（竞品、关键词、选品、追踪、工具）统一继承此类。
    保证所有出站流量均通过带安全防护与熔断机制的 session_mgr 统一路由。
    """
    def __init__(self, session_manager: Optional[SellerSpriteSession] = None):
        self.session_mgr = session_manager or SellerSpriteSession()

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.session_mgr.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.session_mgr.request("POST", url, **kwargs)
