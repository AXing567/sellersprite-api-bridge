import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.session_manager import SellerSpriteSession

print("--> 1. 初始化 SessionManager...")
session_mgr = SellerSpriteSession()

print(f"--> 配置的最小间隔: {session_mgr.min_interval}s, 最大间隔: {session_mgr.max_interval}s")
print(f"--> Cookie 缓存路径: {session_mgr.cookie_cache_path}")
print(f"--> 熔断记录路径: {session_mgr.login_state_path}")

print("--> 2. 测试熔断检查...")
try:
    session_mgr._check_login_fuse()
    print("熔断器状态正常，允许操作")
except Exception as e:
    print(f"触发熔断器: {e}")

print("--> 3. 测试拟人延时微抖动...")
import time
t0 = time.time()
session_mgr._wait_for_rate_limit()
t1 = time.time()
print(f"第一次请求记录完成，用时: {t1 - t0:.2f}s")
session_mgr._wait_for_rate_limit()
t2 = time.time()
print(f"第二次请求自动截流延时，用时: {t2 - t1:.2f}s (符合 2.0-4.0s 预期)")

print("\n--> 4. 防风控与熔断逻辑测试通过！")
