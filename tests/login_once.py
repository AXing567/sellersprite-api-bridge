"""
单次受控登录验证（严格只发起一次登录尝试，绝不重试）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

print("=" * 60)
print("步骤 1: 初始化会话管理器（含防风控检查）")
print("=" * 60)
mgr = SellerSpriteSession()
print(f"账号: {mgr.account}")
print(f"Cookie 缓存: {mgr.cookie_cache_path}")
print(f"熔断状态: {mgr.login_state_path}")

print()
print("=" * 60)
print("步骤 2: 执行单次登录（最多 1 次 signin 请求）")
print("=" * 60)
try:
    ok = mgr.login()
    print(f"登录结果: {ok}")
except Exception as e:
    print(f"登录异常: {type(e).__name__}: {e}")
    sys.exit(1)

if not ok:
    print("登录失败，终止后续操作以避免触发风控")
    sys.exit(1)

print()
print("=" * 60)
print("步骤 3: 输出已获取的 Cookie 凭据")
print("=" * 60)
for k, v in mgr.session.cookies.get_dict().items():
    show = v if len(v) <= 40 else v[:40] + "..."
    print(f"  {k} = {show}")

print()
print("=" * 60)
print("步骤 4: 验证会员身份与额度")
print("=" * 60)
r = mgr.request("GET", "https://www.sellersprite.com/w/user/info", timeout=20)
print(f"状态码: {r.status_code}")
print(f"响应前 500 字符: {r.text[:500]}")
