"""
端到端冒烟测试
------------------------------------------------
用法（服务已启动的前提下）：
    python tests/smoke_test.py

会依次调用各大板块的代表性接口，打印关键字段并给出可用/受限判定。
注意：本脚本只发 HTTP 请求，不涉及登录，不消耗额外凭证。
"""
import json
import sys
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(path, method="GET", body=None):
    url = BASE + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"__error__": f"HTTP {e.code}", "__detail__": e.read().decode("utf-8", "ignore")[:300]}
    except Exception as e:
        return {"__error__": str(e)}


def show(title, ok, detail):
    mark = "✅" if ok else "⚠️ "
    print(f"{mark} {title}")
    print(f"     {detail}")


def main():
    print("=" * 70)
    print("卖家精灵 API 转接桥 —— 端到端冒烟测试")
    print("=" * 70)

    # 0. 健康检查
    h = call("/health")
    if h.get("status") == "ok":
        show("服务健康", True,
             f"账号 {h.get('account')} / 缓存凭证={h.get('has_cached_token')} / 限流 {h.get('rate_limit')}")
        if (h.get("login_fuse") or {}).get("tripped"):
            print(f"     ⚠️ 登录熔断中：{str(h['login_fuse'].get('last_reason'))[:120]}")
    else:
        show("服务健康", False, str(h))
        print("\n服务未启动，请先运行 start.bat 或 start.sh")
        return 1

    asin = "B0CMJTSVRW"

    # 1. 竞品监控
    r = call(f"/api/v1/competitor/monitor-summary?asin={asin}")
    if r.get("core_info"):
        ci, sr, rv = r["core_info"], r.get("sales_rank") or {}, r.get("reviews") or {}
        show("竞品监控聚合", True,
             f"{ci.get('brand')} / ${ci.get('current_price')} / BSR {sr.get('bsr_main_rank')} / "
             f"月销 {sr.get('est_monthly_sales')} / {rv.get('rating')}星 {rv.get('ratings_count')}评分")
    else:
        show("竞品监控聚合", False, str(r)[:200])

    # 2. 关键词挖掘
    q = urllib.parse.quote("yoga mat")
    r = call(f"/api/v1/keywords/research?keyword={q}&size=3")
    if r.get("items"):
        first = r["items"][0]
        show("关键词挖掘", True,
             f"{first.get('keyword')} 月搜 {first.get('monthly_search_volume')} / "
             f"购买率 {first.get('purchase_rate')} / PPC ${first.get('ppc_bid')} / "
             f"需供比 {first.get('supply_demand_ratio')}")
    else:
        show("关键词挖掘", False, str(r.get("notice"))[:200])

    # 3. 选市场
    r = call("/api/v1/market/research?size=2")
    if r.get("items"):
        first = r["items"][0]
        show("细分市场分析", True,
             f"{first.get('market_name')} 月总销 {first.get('monthly_sales_total')} / "
             f"毛利率 {first.get('avg_gross_margin')} / 中国卖家 {first.get('china_seller_ratio')}")
    else:
        show("细分市场分析", False, str(r.get("notice"))[:200])

    # 4. 利润计算器（本地）
    r = call("/api/v1/tools/profit-calculator", "POST", {
        "selling_price": 29.99, "product_cost": 6.5,
        "shipping_weight_pounds": 0.8, "first_leg_shipping": 1.2,
        "advertising_rate": 0.12,
    })
    if "net_profit" in r:
        show("FBA 利润计算器", True,
             f"净利 ${r['net_profit']} / 净利率 {r['net_margin']} / ROI {r['roi']} / 保本价 ${r['break_even_price']}")
    else:
        show("FBA 利润计算器", False, str(r)[:200])

    # 5. 销量预测（本地）
    r = call("/api/v1/tools/sales-estimator?bsr_rank=1500&price=29.99")
    if "est_monthly_sales" in r:
        show("BSR 销量预测", True, f"预估月销 {r['est_monthly_sales']} / 日均 {r['est_daily_sales']}")
    else:
        show("BSR 销量预测", False, str(r)[:200])

    # 6. ABA 出单词反查
    r = call(f"/api/v1/keywords/aba-reverse?asin={asin}")
    if r.get("returned", 0) > 0:
        show("ABA 出单词反查", True,
             f"{r.get('total')} 个出单词，本次返回 {r.get('returned')} 条（周期 {r.get('table_period')}）")
    elif "__error__" not in r:
        show("ABA 出单词反查", True,
             f"返回 0 条（该 ASIN 当期 ABA 无收录，属正常），已给出说明")
    else:
        show("ABA 出单词反查", False, str(r)[:200])

    # 7. 竞品流量词（双通道）
    r = call(f"/api/v1/competitor/traffic-keywords?asin={asin}")
    if r.get("keywords_list"):
        show("竞品流量词（双通道）", True,
             f"来源 {r.get('source')}，{len(r['keywords_list'])} 个词，"
             f"首词点击份额 {r['keywords_list'][0].get('traffic_share')}")
    elif "__error__" not in r:
        show("竞品流量词（双通道）", True, "两通道均空，已给出说明")
    else:
        show("竞品流量词（双通道）", False, str(r)[:200])

    # 8. 选产品（类目节点路径）
    node_path = urllib.parse.quote("1055398:284507:289754:760384:289735:678496011")
    r = call(f"/api/v1/product/filter?node_id_path={node_path}&size=3")
    if r.get("items"):
        first = r["items"][0]
        show("选产品（产品库筛选）", True,
             f"{r.get('returned')} 条 / 首位 {first.get('asin')} "
             f"${first.get('price')} 月销 {first.get('monthly_sales')} "
             f"毛利率 {first.get('gross_margin')} BSR {first.get('bsr_rank')}")
    else:
        show("选产品（产品库筛选）", False, str(r.get("notice"))[:200])

    # 9. 关键词反查（双通道）
    r = call(f"/api/v1/keywords/reverse?asin={asin}&size=10")
    if r.get("items"):
        show("关键词反查（双通道）", True,
             f"来源 {r.get('source')} / 总数 {r.get('total')} / 返回 {r.get('returned')} / "
             f"首词 {r['items'][0].get('keyword')[:26]!r}")
    elif "__error__" not in r:
        show("关键词反查（双通道）", True, "两通道均空，已给出说明")
    else:
        show("关键词反查（双通道）", False, str(r)[:200])

    # 10. 关键词收录检测
    kws = "keywords=wireless+mics+for+iphone&keywords=yoga+mat"
    r = call(f"/api/v1/keywords/checker?asin={asin}&{kws}")
    if r.get("checked"):
        show("关键词收录检测", True,
             f"来源 {r.get('source')} / 检测 {r.get('checked')} 词 / 命中 {r.get('indexed_count')} 词")
    elif "__error__" not in r:
        show("关键词收录检测", True, "反查通道为空，已给出说明")
    else:
        show("关键词收录检测", False, str(r)[:200])

    print()
    print("=" * 70)
    print("说明：ABA 出单词反查对部分 ASIN 会返回 0 条（该 ASIN 当期无 ABA 收录），")
    print("      属数据本身情况，不是接口故障。")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
