# 卖家精灵 API 转接桥 (SellerSprite API Bridge)

把**卖家精灵网页版会员能力**封装成**标准 REST API**，可部署在 Windows / Linux / Docker。

填入账号密码即可用，不用买官方 API 套餐。

---

## 一、能力清单（18 个接口）

| 板块 | 接口 | 说明 | 状态 |
|---|---|---|---|
| **竞品监控** | `GET /api/v1/competitor/core-info` | 标题/主图/品牌/价格/发货方式/上架时间 | ✅ 实测可用 |
| | `GET /api/v1/competitor/sales-rank` | BSR 排名/预估月销量/月销售额/日均销量 | ✅ 实测可用 |
| | `GET /api/v1/competitor/promotions` | 标价/Coupon/秒杀/券后到手价 | ✅ 实测可用 |
| | `GET /api/v1/competitor/reviews` | 星级/评分数/月新增评分 | ✅ 实测可用 |
| | `GET /api/v1/competitor/traffic-keywords` | 流量词总数/自然与广告占比/词表（**双通道自动降级**） | ✅ 实测可用 |
| | `GET /api/v1/competitor/monitor-summary` | **顶层聚合**，一次拿全维度 | ✅ 实测可用 |
| **关键词** | `GET /api/v1/keywords/research` | 月搜索量/购买率/点击集中度/PPC竞价/需供比 | ✅ 实测可用 |
| | `GET /api/v1/keywords/aba-reverse` | ABA 出单词反查（点击/转化份额） | ✅ 实测可用 |
| | `GET /api/v1/keywords/reverse` | 关键词反查：ASIN → 全量曝光词（**双通道自动降级**） | ✅ 实测可用 |
| | `GET /api/v1/keywords/checker` | 关键词收录检测（自然位/广告位） | ✅ 实测可用（反查命中判定） |
| **选品选市** | `GET /api/v1/market/research` | 细分市场大盘：垄断度/新品占比/**平均毛利率**/退货率 | ✅ 实测可用 |
| | `GET /api/v1/product/filter` | 产品库多维度筛选（类目/销量/价格/毛利率/评分） | ✅ 实测可用 |
| **监控追踪** | `GET /api/v1/tracking/products` | 读取网页端已建的产品监控 | ⚠️ 只读，需网页端先添加 |
| | `GET /api/v1/tracking/keywords` | 读取词排名监控 | ⚠️ 只读，需网页端先添加 |
| | `GET /api/v1/tracking/stores` | 读取竞店监控 | ⚠️ 只读，需网页端先添加 |
| **算法工具** | `POST /api/v1/tools/profit-calculator` | FBA 利润全拆解 + 保本售价 | ✅ 本地计算，零额度 |
| | `GET /api/v1/tools/sales-estimator` | BSR → 月销量幂律估算 | ✅ 本地计算，零额度 |
| **运维** | `GET /health` | Cookie 缓存/熔断/限流状态自检 | ✅ |

> ✅ = 真实数据跑通　⚠️ = 接口与解析已就绪，但受账号额度/参数限制暂未出数据（会返回 `notice` 说明原因，**绝不造假数据**）

---

## 二、部署

### Windows（最简单）
1. 安装 Python 3.9+
2. 双击 `start.bat`（首次会自动建虚拟环境 + 装依赖 + 生成 config.json）
3. 编辑 `config.json` 填账号密码，再次运行 `start.bat`
4. 打开 <http://127.0.0.1:8000/docs>

### Linux
```bash
chmod +x start.sh && ./start.sh
```

### Docker
```bash
cp config.example.json config.json   # 填账号密码
docker compose up -d
curl http://127.0.0.1:8000/health
```

---

## 三、配置说明 `config.json`

```json
{
  "server": { "host": "0.0.0.0", "port": 8000 },
  "sellersprite": {
    "account": "你的手机号",
    "password": "你的密码",
    "default_marketplace": "US",
    "user_agent": "Mozilla/5.0 ..."
  },
  "security": {
    "cookie_cache_path": "data/session_cookies.json",
    "cookie_ttl_hours": 168,
    "min_request_interval_seconds": 2.0,
    "max_request_interval_seconds": 4.0,
    "max_login_retries_per_day": 3,
    "login_cooldown_minutes": 30,
    "enable_request_jitter": true
  }
}
```

`security` 段是**防封核心**，改动前请读完下一节。

---

## 四、防封机制（这是本项目的关键设计）

卖家精灵对"短时间高频登录"有风控，触发后账号会被锁定，需要人工找回密码才能解锁。本项目内置 4 层防护：

1. **Cookie 持久化（7 天 TTL）**
   登录成功一次后，凭据写入 `data/session_cookies.json`。
   之后无论重启服务、跑测试、发新请求，**只要缓存有效就绝不调登录接口**。

2. **登录熔断**
   24 小时内登录失败 ≥3 次 → 进入 30 分钟强制冷静期，直接抛错拒绝重试。
   识别到"账号已锁定""需要验证码"等字样 → 立即停止，不盲目撞库。

3. **拟人请求抖动**
   所有出站请求之间强制插入 2~4 秒随机延时，抹掉机械化的高频特征。

4. **并发防重锁**
   多线程统一收敛到受控会话层，同一时刻只有一个登录动作。

> 上一次事故就是因为早期探针脚本**每个脚本各自登录一次**，几分钟内打了 7 次登录接口。现在这类操作在架构上已被禁止。

随时可用 `GET /health` 查看当前是否处于熔断冷却期。

---

## 五、当前已知限制（诚实说明）

| 现象 | 原因 | 处理 |
|---|---|---|
| 所有依赖登录的接口返回 **503 `session_expired`** | `config.json` 里的账号/密码被卖家精灵判定为**密码错误**（已连续错 2 次，官网 10 次即锁号） | 不会自动重试（避免锁号）。请在官网确认能正常登录后，把新密码写进 `config.json`；熔断冷却结束后会自动重试一次 |
| 所有依赖登录的接口返回 **429 熔断** | 24 小时内登录失败达阈值，进入 30 分钟强制冷静期 | 先修正凭证再等冷却，**不要反复调用**。`GET /health` 的 `warning` 字段会直说原因 |
| `reverse` / `traffic-keywords` 的 `source` 字段为 `aba-reverse` | 官网「关键词反查」(`/v2/keyword-reverse/.../more`) 对当前试用账号恒定返回空结果（`total=0, items=[]`，HTTP 仍是 200）。已排除参数问题：`station` 路径解析正常（US→GLOBAL、JP→JAPAN、DE→GERMANY 均正确回显），variation 接口也能正常返回变体列表但每个变体 `total` 均为 0，说明是**账号套餐权益**层面的限制（该账号 `valid-pay-status=false`，属试用套餐） | 已做**双通道自动降级**：主通道空时自动切「ABA 出单词反查」，返回体 `source` + `notice` 明示来源与字段差异。换成含该权益的付费账号后，主通道会自动生效，无需改代码 |
| `checker` 的 `organic_rank` 为 `null` | 网页版「关键词收录检测」是两步式接口（POST 建任务拿 `flag` → 轮询 `result/{flag}`），且 `/v2/keyword-checker/*` 子路由在该账号下直接 404，无法稳定抓取 | 已改为**反查命中判定**：拉该 ASIN 全部曝光词后逐一比对传入词，命中即「已收录」，每个词的判定依据写在 `evidence` 字段 |
| `tracking/*` 返回 0 条 | 该账号网页端还没添加任何监控对象；**且该模块尚未用真实数据验收** | 在网页端添加后可读取。已加表头健全性校验：若拿到的表不是该模块的表（官网 `product-tracking` 有时会回关键词监控的列），直接返回 `notice` 拒绝解析，不输出错位数据 |
| `size` 参数对官网无效 | 卖家精灵固定返回整页（50 条） | 已改为本地截断，行为符合预期 |

---

## 五之二、逆向过程中踩过并已修复的关键坑（给后来者）

| 坑 | 表现 | 正解 |
|---|---|---|
| **会话失效不一定返回 302** | 官网掉线时直接 HTTP 200 返回登录页（约 62KB）。业务层把登录页当表格解析 → 空结果 → 报成「没有数据 / 会员额度不足」，排查成本极高 | `session_manager.is_login_html()` 识别登录页标题/登签表单，命中即抛 `SessionExpiredError`（HTTP 503），**绝不把登录页当业务数据返回** |
| **`密码错误` 被误判成「账号已锁定」** | 原文案是「密码错误…连续 10 次将锁定」，含"锁定"两个字就被归到锁定分支，提示去"重置密码解锁"，方向完全错 | 错误分类优先级：`密码错误/账号或密码/用户不存在` → 凭证失效，**立即停止重试**；`已锁定` / `验证码` / `过于频繁` 分属不同分支 |
| **同一轮登录失败被计数两次** | 先在分支里 `_record_login_result(False)` 再 raise，外层 `except` 又记一次，2 次尝试就顶到 4 次，熔断被误触发 | 加 `recorded` 标志位，一次尝试只计一次 |
| `order.field` 是**枚举值**不是自由文本 | 传 `units` 服务端不报错，直接返回「暂无结果」空页，极易误判成"接口不通" | 合法值只有 `total_units / total_amount / bsr_rank / price / rating / profit` |
| 选产品端点少了 `/monthly` | `/v2/product-research` 只是入口页，永远没有数据 | 真实端点 `GET /v2/product-research/monthly`，且必须带 `nodeIdPath`（冒号分隔完整路径），只传 `nodeId` 无效 |
| `<tr>` 未正确嵌套 `<tbody>` | BeautifulSoup 遍历 tbody 只能拿到 1 行商品 | 新增 `parser.extract_rows_loose()`，正则扫全文 `<tr>` 再逐 td 重建 DOM，稳定拿 20~50 条 |
| 选市场的深度指标整行丢失 | 毛利率/中国卖家占比/A+ 占比全变 `null` | 「完整市场路径」展开行是 `<td colspan="15">` 单单元格，`min_cells` 阈值必须放到 1；`nodeIdPath` 只存在于 `<a href>` 里，纯文本取不到，要读 DOM |

---

## 六、接口示例

```bash
# 竞品全维度聚合
curl "http://127.0.0.1:8000/api/v1/competitor/monitor-summary?asin=B0CMJTSVRW"

# 关键词挖掘（找月搜 10 万+ 的词）
curl "http://127.0.0.1:8000/api/v1/keywords/research?keyword=yoga+mat&size=20&min_search_volume=100000"

# 选市场（看哪个细分市场毛利率高、中国卖家还没挤满）
curl "http://127.0.0.1:8000/api/v1/market/research?size=50"

# 选产品（用上一步返回的 node_id_path 深挖该细分市场里的高潜商品）
curl "http://127.0.0.1:8000/api/v1/product/filter?node_id_path=1055398:284507:289754:760384:289735:678496011&min_sales=500&min_profit=40&size=20"

# 关键词反查（ASIN 的全部曝光词；主通道无权益时自动降级 ABA）
curl "http://127.0.0.1:8000/api/v1/keywords/reverse?asin=B0CMJTSVRW&size=50"

# 关键词收录检测
curl "http://127.0.0.1:8000/api/v1/keywords/checker?asin=B0CMJTSVRW&keywords=wireless+mics+for+iphone&keywords=yoga+mat"

# FBA 利润测算
curl -X POST "http://127.0.0.1:8000/api/v1/tools/profit-calculator" \
  -H "Content-Type: application/json" \
  -d '{"selling_price":29.99,"product_cost":6.5,"shipping_weight_pounds":0.8,
       "first_leg_shipping":1.2,"advertising_rate":0.12}'
```

实测返回示例（真实数据）：

```json
{
  "asin": "B0CMJTSVRW",
  "core_info": { "brand": "Mini Mic Pro", "current_price": 24.99, "fulfillment_type": "FBA" },
  "sales_rank": { "bsr_main_rank": 5, "est_monthly_sales": 30305, "est_monthly_revenue": 757322.0 },
  "reviews": { "rating": 4.3, "ratings_count": 9831, "monthly_ratings_increment": 322 }
}
```

选产品实测（`node_id_path=1055398:284507:289754:760384:289735:678496011`，销量降序）：

```json
{
  "returned": 20, "has_more": true, "order_field": "total_units", "month_name": "bsr_sales_nearly",
  "items": [{
    "rank": 1, "asin": "B08SGPWY8Z", "parent_asin": "B0GWFS1KL9",
    "title": "Collapsible Bucket for Cleaning - 7.27L Foldable Wash Bin Dish Tub ... (Green)",
    "brand": "Wakeman", "badges": ["A+", "V", "BS", "AC"],
    "price": 12.23, "qa_count": 37,
    "bsr_rank": 1820, "bsr_growth": -73, "bsr_growth_rate": -0.04,
    "monthly_sales": 3404, "sales_growth": 0.33,
    "monthly_revenue": 41631.0, "revenue_growth": 0.33,
    "gross_margin": 0.19, "fba_fee": 8.02,
    "rating": 4.6, "rating_monthly_new": 25, "ratings_count": 8901, "review_rate": 0.0073,
    "release_date": "2021-01-08", "listing_age": "5年9个月",
    "seller_type": "AMZ", "buyer_shipping_fee": -1.0
  }]
}
```

---

## 七、目录结构

```
sellersprite-api-bridge/
├── start.bat / start.sh          # 一键启动
├── Dockerfile / docker-compose.yml
├── config.json                   # 真实配置（.gitignore 保护）
├── config.example.json           # 脱敏模板
├── requirements.txt
├── data/                         # Cookie 缓存、熔断状态、调试快照（勿删勿提交）
├── docs/00_MASTER_PLAN.md        # 全功能实施方案与进度
├── src/
│   ├── api/
│   │   ├── server.py             # FastAPI 入口 + 全局异常兜底
│   │   └── routers/              # competitor / keywords / product / tracking / tools
│   ├── core/
│   │   ├── session_manager.py    # 登录 + Cookie 持久化 + 熔断 + 抖动
│   │   ├── base_client.py        # 统一受控请求入口
│   │   └── parser.py             # 表头驱动的 HTML 表格解析器
│   ├── modules/                  # 业务逻辑与字段清洗
│   └── schemas/                  # Pydantic 强类型响应模型
└── tests/                        # 探针与联调脚本
```

---

## 八、开发者备注

- **不要**在测试脚本里各自 `session.post(SIGNIN_URL)`。统一走 `SellerSpriteSession`。
- 调试页面结构时，先把 HTML 存到 `data/debug/`，离线分析，避免反复请求。
- `data/session_cookies.json` 里是登录凭据，等同密码，泄露即等于账号泄露。
