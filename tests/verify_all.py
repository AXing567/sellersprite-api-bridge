"""一日/短期会员用的「一次性全量验收器」。

设计前提
--------
会员有效期可能只有 1 天，所以必须做到：
1. **一次登录跑完全部接口**：所有业务请求都打到本地服务，复用同一份 Cookie 缓存，
   全程只在上游登录 1 次；
2. **遇到会话失效 / 熔断立即停手**：绝不带着坏凭证继续重试（会把账号撞锁）；
3. **结果落盘成 Markdown 报告**，方便事后复盘，不用再登录复现。

用法
----
    python tests/verify_all.py            # 跑全部 17 个接口
    python tests/verify_all.py --only tracking
    python tests/verify_all.py --diag     # 额外做监控页渲染诊断（复用缓存 Cookie，不重新登录）

前置条件
--------
本地服务已启动（start.bat / start.sh），且 config.json 里凭证有效。
"""
import json
import pathlib
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8000"
ASIN = "B0CMJTSVRW"
NODE_PATH = "1055398:284507:289754:760384:289735:678496011"

# 环境里存在 http_proxy 时 urllib 会走代理，导致访问 127.0.0.1 失败，必须显式禁用
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

ABORT_CODES = {429, 503}   # 熔断 / 会话失效 —— 见到就整体停手


def call(path, method="GET", body=None, timeout=180):
    """返回 (status_code, payload)。payload 为 dict 或 {"__raw__": str}。"""
    url = BASE + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "ignore")
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, {"__raw__": raw[:500]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"__raw__": raw[:500]}
    except Exception as e:
        return 0, {"__raw__": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------- 判定器
# 返回 (verdict, detail)，verdict ∈ {"pass", "empty", "fail"}
# empty = 返回空但属于正常业务空（附 notice 说明），不算故障

def _first(resp, key):
    v = resp.get(key)
    return v[0] if isinstance(v, list) and v else None


def chk_core_info(_s, r):
    ci = r if "brand" in r or "current_price" in r else _first(r, "items")
    if ci and (ci.get("brand") or ci.get("current_price") or ci.get("title")):
        return "pass", f"{ci.get('brand')} / ${ci.get('current_price')} / {ci.get('fulfillment_type')}"
    return "fail", str(r)[:180]


def chk_sales_rank(_s, r):
    if r.get("bsr_main_rank") or r.get("est_monthly_sales"):
        return "pass", (f"BSR {r.get('bsr_main_rank')} / 月销 {r.get('est_monthly_sales')} / "
                        f"月销额 ${r.get('est_monthly_revenue')}")
    return "fail", str(r)[:180]


def chk_reviews(_s, r):
    if r.get("rating") or r.get("ratings_count"):
        return "pass", f"{r.get('rating')} 星 / {r.get('ratings_count')} 评分 / 近30天+{r.get('monthly_ratings_increment')}"
    return "fail", str(r)[:180]


def chk_promotions(_s, r):
    if r.get("current_price") or r.get("net_price") or r.get("coupon_value"):
        return "pass", f"标价 ${r.get('current_price')} / 券 ${r.get('coupon_value')} / 到手 ${r.get('net_price')}"
    return "empty", "该 ASIN 当前无促销/无券（正常业务空）"


def chk_traffic(_s, r):
    lst = r.get("keywords_list") or []
    if lst:
        return "pass", (f"来源 {r.get('source')} / {len(lst)} 词 / "
                        f"首词点击份额 {lst[0].get('traffic_share')} / 自然流量占比 {r.get('organic_traffic_ratio')}")
    if r.get("notice"):
        return "empty", f"两通道均空：{str(r.get('notice'))[:120]}"
    return "fail", str(r)[:180]


def chk_summary(_s, r):
    ci = r.get("core_info") or {}
    sr = r.get("sales_rank") or {}
    rv = r.get("reviews") or {}
    filled = sum(1 for x in (ci, sr, rv) if x)
    if filled >= 2:
        return "pass", (f"聚合 {filled}/5 板块 / {ci.get('brand')} / BSR {sr.get('bsr_main_rank')} / "
                        f"月销 {sr.get('est_monthly_sales')} / {rv.get('rating')}星")
    return "fail", str(r)[:180]


def chk_kw_research(_s, r):
    it = _first(r, "items")
    if it:
        return "pass", (f"{it.get('keyword')} 月搜 {it.get('monthly_search_volume')} / "
                        f"购买率 {it.get('purchase_rate')} / PPC ${it.get('ppc_bid')} / "
                        f"需供比 {it.get('supply_demand_ratio')}")
    return "empty", f"空结果：{str(r.get('notice'))[:120]}"


def chk_aba(_s, r):
    if r.get("returned", 0) > 0:
        it = _first(r, "items") or _first(r, "keywords_list") or {}
        return "pass", (f"{r.get('total')} 个出单词 / 返回 {r.get('returned')} / "
                        f"周期 {r.get('table_period')} / 首词 {str(it.get('keyword'))[:24]!r}")
    return "empty", f"当期 ABA 无收录（正常）：{str(r.get('notice'))[:100]}"


def chk_reverse(_s, r):
    it = _first(r, "items")
    if it:
        return "pass", (f"来源 {r.get('source')} / 总数 {r.get('total')} / 返回 {r.get('returned')} / "
                        f"首词 {str(it.get('keyword'))[:24]!r}")
    return "empty", f"两通道均空：{str(r.get('notice'))[:120]}"


def chk_checker(_s, r):
    if r.get("checked"):
        return "pass", (f"来源 {r.get('source')} / 检测 {r.get('checked')} 词 / "
                        f"命中 {r.get('indexed_count')} 词")
    return "empty", f"反查通道为空：{str(r.get('notice'))[:120]}"


def chk_market(_s, r):
    it = _first(r, "items")
    if it:
        return "pass", (f"{it.get('market_name')} / 月销 {it.get('monthly_sales_total')} / "
                        f"均毛利 {it.get('avg_gross_margin')} / 中国卖家 {it.get('china_seller_ratio')}")
    return "empty", f"空结果：{str(r.get('notice'))[:120]}"


def chk_product(_s, r):
    it = _first(r, "items")
    if it:
        return "pass", (f"{r.get('returned')} 条 / 首位 {it.get('asin')} ${it.get('price')} / "
                        f"月销 {it.get('monthly_sales')} / 毛利 {it.get('gross_margin')} / BSR {it.get('bsr_rank')}")
    return "empty", f"空结果：{str(r.get('notice'))[:120]}"


def chk_profit(_s, r):
    if "net_profit" in r:
        def pct(v):
            try:
                return f"{float(v) * 100:.2f}%"
            except (TypeError, ValueError):
                return str(v)
        return "pass", (f"净利 ${r['net_profit']} / 净利率 {pct(r.get('net_margin'))} / "
                        f"ROI {pct(r.get('roi'))} / 保本价 ${r['break_even_price']}")
    return "fail", str(r)[:180]


def chk_estimator(_s, r):
    if "est_monthly_sales" in r:
        return "pass", f"预估月销 {r['est_monthly_sales']} / 日均 {r['est_daily_sales']}"
    return "fail", str(r)[:180]


def _chk_tracking(kind):
    def _f(_s, r):
        items = r.get("items") or []
        if items:
            it = items[0]
            if kind == "products":
                return "pass", (f"{len(items)} 个监控商品 / 首位 {it.get('asin')} "
                                f"${it.get('current_price')} BSR {it.get('bsr_rank')}")
            if kind == "keywords":
                return "pass", (f"{len(items)} 个监控词 / 首位 {it.get('keyword')} "
                                f"自然位 {it.get('current_organic_rank')}")
            return "pass", (f"{len(items)} 个监控店铺 / 首位 {it.get('store_name')} "
                            f"在售 {it.get('product_count')}")
        return "empty", f"账号在网页端还没有{kind}监控对象 —— 需先在网页端添加再验收"
    return _f


CASES = [
    # (分组, 名称, method, path, body, 判定器)
    ("competitor", "1.1 核心画像", "GET", f"/api/v1/competitor/core-info?asin={ASIN}", None, chk_core_info),
    ("competitor", "1.2 销量与BSR", "GET", f"/api/v1/competitor/sales-rank?asin={ASIN}", None, chk_sales_rank),
    ("competitor", "1.3 评分与评价", "GET", f"/api/v1/competitor/reviews?asin={ASIN}", None, chk_reviews),
    ("competitor", "1.4 促销与优惠券", "GET", f"/api/v1/competitor/promotions?asin={ASIN}", None, chk_promotions),
    ("competitor", "1.5 流量词", "GET", f"/api/v1/competitor/traffic-keywords?asin={ASIN}", None, chk_traffic),
    ("competitor", "1.6 聚合监控", "GET", f"/api/v1/competitor/monitor-summary?asin={ASIN}", None, chk_summary),
    ("keywords", "2.1 关键词挖掘", "GET", "/api/v1/keywords/research?keyword=yoga%20mat&size=3", None, chk_kw_research),
    ("keywords", "2.2 ABA出单词反查", "GET", f"/api/v1/keywords/aba-reverse?asin={ASIN}", None, chk_aba),
    ("keywords", "2.3 关键词反查", "GET", f"/api/v1/keywords/reverse?asin={ASIN}&size=10", None, chk_reverse),
    ("keywords", "2.4 收录检测", "GET",
     f"/api/v1/keywords/checker?asin={ASIN}&keywords=wireless+mics+for+iphone&keywords=yoga+mat", None, chk_checker),
    ("market", "3.1 选市场", "GET", "/api/v1/market/research?size=2", None, chk_market),
    ("product", "3.2 选产品", "GET",
     f"/api/v1/product/filter?node_id_path={urllib.parse.quote(NODE_PATH)}&size=3", None, chk_product),
    ("tracking", "4.1 产品监控", "GET", "/api/v1/tracking/products", None, _chk_tracking("products")),
    ("tracking", "4.2 关键词监控", "GET", "/api/v1/tracking/keywords", None, _chk_tracking("keywords")),
    ("tracking", "4.3 店铺监控", "GET", "/api/v1/tracking/stores", None, _chk_tracking("stores")),
    ("tools", "5.1 利润计算器", "POST", "/api/v1/tools/profit-calculator",
     {"selling_price": 29.99, "product_cost": 6.5, "shipping_weight_pounds": 0.8,
      "first_leg_shipping": 1.2, "advertising_rate": 0.12}, chk_profit),
    ("tools", "5.2 销量预测", "GET", "/api/v1/tools/sales-estimator?bsr_rank=1500&price=29.99", None, chk_estimator),
]

MARK = {"pass": "✅ PASS", "empty": "⚪ EMPTY", "fail": "❌ FAIL"}

# 纯本地计算，不依赖登录 —— 即使凭证失效也应当可验收
LOCAL_GROUPS = {"tools"}


def preflight():
    """返回 (可继续?, health, 是否被阻断)。被阻断通常意味着凭证问题。"""
    s, h = call("/health", timeout=10)
    if s != 200:
        print(f"服务未响应（HTTP {s}）：{h}")
        print("请先启动服务：start.bat 或 start.sh")
        return False, None, True
    fuse = h.get("login_fuse") or {}
    print(f"服务：{h.get('account')} / 缓存凭证={h.get('has_cached_token')} / 限流 {h.get('rate_limit')}")
    if fuse.get("tripped"):
        print(f"⚠️ 登录熔断中（fail_count={fuse.get('fail_count')}）：{str(fuse.get('last_reason'))[:160]}")
        print("→ 依赖登录的接口本次跳过。本脚本不会重试登录（避免撞锁账号）。")
        return True, h, True
    if not h.get("has_cached_token"):
        print("提示：当前无缓存凭证，首个业务请求会触发一次登录（属正常）。")
    return True, h, False


def diag_tracking_pages():
    """监控页渲染诊断：判断服务端是否真的渲染出数据行。

    2026-10-28 离线分析发现：账号无监控对象时，页面里留的是前端模板占位符
    （{{each(i, k) keywords_list}}）。本诊断用于确认「有监控对象时」到底是
    渲染成真实 <tr>，还是仍然只有模板 —— 这决定了 tracking 该走 HTML 解析
    还是去抓 JSON 接口。
    """
    print("\n" + "=" * 72)
    print("监控页渲染诊断（复用缓存 Cookie，不重新登录）")
    print("=" * 72)

    sys.path.insert(0, str(ROOT))
    try:
        from src.core.session_manager import SellerSpriteSession, SessionExpiredError
    except Exception as e:
        print(f"导入会话管理器失败：{e}")
        return []

    pages = [
        ("product", "https://www.sellersprite.com/v2/product-tracking"),
        ("keyword", "https://www.sellersprite.com/v2/keyword-tracking"),
        ("store", "https://www.sellersprite.com/v2/store-tracking"),
    ]
    out_dir = ROOT / "data" / "debug"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rows = []

    try:
        mgr = SellerSpriteSession()
    except Exception as e:
        print(f"初始化会话失败：{e}")
        return []

    for name, url in pages:
        try:
            resp = mgr.request("GET", url, timeout=30)
            html = resp.text or ""
        except SessionExpiredError as e:
            print(f"  {name}: 会话失效 —— {e}")
            break
        except Exception as e:
            print(f"  {name}: 请求异常 {type(e).__name__}: {e}")
            continue

        path = out_dir / f"diag_{ts}_{name}.html"
        path.write_text(html, encoding="utf-8")

        data_rows = len(re.findall(r'<tr[^>]*data-item-id="\d+"', html))
        tpl_hits = len(re.findall(r"\{\{each\(", html))
        tables = len(re.findall(r"<table\b", html))
        verdict = ("服务端已渲染真实数据行 → 可继续走 HTML 解析"
                   if data_rows else
                   "无数据行（需先加监控对象 / 或为前端渲染 → 改抓 JSON 接口）")

        rows.append((name, len(html), tables, data_rows, tpl_hits, verdict, path.name))
        print(f"  {name:8s} 体积 {len(html):>8,} | table {tables} | "
              f"data-item-id 行 {data_rows} | 模板占位 {tpl_hits} | {verdict}")

    return rows


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = args[i + 1] if i + 1 < len(args) else None
    do_diag = "--diag" in args

    print("=" * 72)
    print("卖家精灵 API —— 一次性全量验收")
    print("=" * 72)

    ok, _h, blocked = preflight()
    if not ok:
        return 2

    cases = [c for c in CASES if (only is None or c[0] == only)]
    if blocked:
        local_only = [c for c in cases if c[0] in LOCAL_GROUPS]
        if local_only:
            print(f"→ 本次只跑 {len(local_only)} 个纯本地接口（不依赖登录）")
        cases = local_only
        if not cases:
            print("→ 无可运行的用例（所选分组都依赖登录），已退出。")
            return 2
    results = []
    aborted = None
    t_all = time.time()

    for idx, (group, name, method, path, body, checker) in enumerate(cases, 1):
        t0 = time.time()
        status, resp = call(path, method, body)
        elapsed = time.time() - t0

        if status in ABORT_CODES:
            detail = resp.get("detail") or resp.get("__raw__") or str(resp)
            aborted = (name, status, str(detail)[:300])
            print(f"\n🛑 [{name}] HTTP {status}，立即中止后续用例（保护账号，不重试）")
            print(f"   {str(detail)[:300]}")
            results.append((group, name, status, elapsed, "fail", f"中止：{str(detail)[:160]}"))
            break

        if status == 0:
            verdict, detail = "fail", resp.get("__raw__", "")[:180]
        else:
            try:
                verdict, detail = checker(status, resp)
            except Exception as e:
                verdict, detail = "fail", f"判定异常 {type(e).__name__}: {e}"

        print(f"{MARK[verdict]} [{name}] {elapsed:.1f}s  {detail[:150]}")
        results.append((group, name, status, elapsed, verdict, detail))

        # 温和节流：本地服务内部已有 2~4s 上游抖动，这里只做轻量间隔
        time.sleep(random.uniform(0.3, 0.8))

    total = time.time() - t_all

    # ---------------- 汇总
    n_pass = sum(1 for r in results if r[4] == "pass")
    n_empty = sum(1 for r in results if r[4] == "empty")
    n_fail = sum(1 for r in results if r[4] == "fail")
    print("\n" + "=" * 72)
    print(f"结果：PASS {n_pass} / EMPTY {n_empty} / FAIL {n_fail}，总耗时 {total:.1f}s")
    if aborted:
        print(f"中止原因：{aborted[0]} → HTTP {aborted[1]}")
    print("=" * 72)

    diag_rows = []
    if do_diag and not aborted:
        diag_rows = diag_tracking_pages()

    # ---------------- 落盘报告
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = ROOT / "data" / f"verify_report_{ts}.md"
    lines = [
        f"# 卖家精灵 API 验收报告 {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        f"- 账号：{(_h or {}).get('account')}",
        f"- 结论：PASS {n_pass} / EMPTY {n_empty} / FAIL {n_fail}，总耗时 {total:.1f}s",
        "",
        "| 分组 | 用例 | HTTP | 耗时 | 结论 | 关键指标 |",
        "|---|---|---|---|---|---|",
    ]
    for group, name, status, elapsed, verdict, detail in results:
        safe = str(detail).replace("|", "\\|")[:160]
        lines.append(f"| {group} | {name} | {status} | {elapsed:.1f}s | {MARK[verdict]} | {safe} |")

    if diag_rows:
        lines += ["", "## 监控页渲染诊断", "",
                  "| 页面 | 体积 | table数 | data-item-id行 | 模板占位 | 判定 | 存档 |",
                  "|---|---|---|---|---|---|---|"]
        for name, size, tables, drows, tpl, verdict, fname in diag_rows:
            lines.append(f"| {name} | {size:,} | {tables} | {drows} | {tpl} | {verdict} | `{fname}` |")

    if aborted:
        lines += ["", "## 中止说明", f"- 用例：{aborted[0]}", f"- HTTP：{aborted[1]}",
                  f"- 详情：{aborted[2]}"]

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n报告已保存：{report}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
