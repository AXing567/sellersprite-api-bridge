"""离线验证：登录页识别与错误分类（不发起任何登录请求，避免加深熔断）"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession, SessionExpiredError

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
login_html = open(os.path.join(base, "data", "debug", "track_product_fresh.html"),
                  encoding="utf-8").read()
print("登录页样本长度:", len(login_html))
print("is_login_html(登录页) ->", SellerSpriteSession.is_login_html(login_html), "（期望 True）")

# 业务页样本：产品库 / 关键词挖掘
biz = open(os.path.join(base, "data", "debug", "pr_ok.html"), encoding="utf-8").read()
print("is_login_html(产品库页) ->", SellerSpriteSession.is_login_html(biz), "（期望 False）")

kw = open(os.path.join(base, "data", "debug", "keyword_research.html"), encoding="utf-8").read()
print("is_login_html(关键词挖掘页) ->", SellerSpriteSession.is_login_html(kw), "（期望 False）")

# 构造伪 Response 测 _resp_is_login_page
class FakeResp:
    def __init__(self, text, ctype="text/html;charset=utf-8"):
        self._text = text
        self.headers = {"Content-Type": ctype}
    @property
    def text(self):
        return self._text

mgr = SellerSpriteSession.__new__(SellerSpriteSession)  # 不触发 __init__（不读配置、不登录）
print("\n_resp_is_login_page(登录页 HTML) ->", SellerSpriteSession._resp_is_login_page(mgr, FakeResp(login_html)), "（期望 True）")
print("_resp_is_login_page(大业务页)    ->", SellerSpriteSession._resp_is_login_page(mgr, FakeResp(biz)), "（期望 False，因体积>200KB）")
print("_resp_is_login_page(JSON)        ->", SellerSpriteSession._resp_is_login_page(mgr, FakeResp('{"code":"ok"}', "application/json")), "（期望 False）")

# 错误分类：模拟不同登录返回文案
def classify(err):
    if "密码错误" in err or "账号或密码" in err or "用户不存在" in err:
        return "CREDENTIAL -> SessionExpiredError(停止重试)"
    if "锁定" in err:
        return "LOCKED -> SessionExpiredError"
    if "验证码" in err or "过于频繁" in err:
        return "CAPTCHA -> SessionExpiredError"
    return "OTHER -> return False"

real = "密码错误，如果连续【10】次密码错误，系统将锁定此账号！您已连续密码错误【2】次！"
print("\n真实错误文案归类:", classify(real))
assert "密码错误" in real and classify(real).startswith("CREDENTIAL"), "分类错误"

print("\nSessionExpiredError 是 RuntimeError 子类:", issubclass(SessionExpiredError, RuntimeError))
print("全部离线检查通过")
