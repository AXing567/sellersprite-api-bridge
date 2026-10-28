# 卖家精灵网页版全功能 API 化实施方案与执行路线图 (Master Roadmap)

> **项目目标**：将卖家精灵（SellerSprite）网页版会员的所有核心数据与工具功能，全面逆向封装为标准的、可部署于 Windows / Linux / Docker 的现代化 REST API 服务。采用 **“原子接口细粒度解耦 + 场景化顶层聚合”** 的架构模式。

---

## 🏛️ 系统架构设计规范

```text
sellersprite-api-bridge/
├── config.json                 # 账号密码、端口、超时、代理配置
├── src/
│   ├── api/
│   │   ├── routers/            # 路由层：按六大业务板块组织
│   │   │   ├── competitor.py   # 板块 1: 竞品反查与监控
│   │   │   ├── keywords.py     # 板块 2: 关键词挖掘与收录
│   │   │   ├── product.py      # 板块 3: 选产品与选市场
│   │   │   ├── tracking.py     # 板块 4: 监控看板 (产品/词/店铺)
│   │   │   ├── tools.py        # 板块 5: 实用辅助工具 (销量预测/利润计算)
│   │   │   └── user.py         # 板块 6: 账号会话与额度管理
│   │   └── server.py           # FastAPI 主程序入口
│   ├── core/                   # 核心地基
│   │   ├── session_manager.py  # 自动模拟登录、Token/Cookie续期、并发连接池
│   │   └── base_client.py      # 网页端通用请求器、重试机制、错误处理
│   ├── modules/                # 业务逻辑与网页端数据解析层
│   └── schemas/                # Pydantic 强类型请求/响应规范
```

---

## 🗺️ 全功能拆解与分步执行计划

整个项目划分为 **6 大功能板块、18 个标准里程碑任务**。每个任务都按照 **“字段定义 -> 逆向接口分析 -> 解析器编写 -> FastAPI 路由注册 -> 端到端验证”** 的闭环节奏执行。

---

### 第一阶段：地基稳固与竞品监控板块（已完成核心，待补齐子项）

- [x] **任务 1.1：登录态与会话管理引擎 (`session_manager`)**
  - 支持账号密码 MD5 加密模拟登录。
  - 自动管理与维系 `Sprite-X-Token`、`rank-login-user` 会话。
  - 支持 302 掉线自动无感重登。
- [x] **任务 1.2：竞品画像原子接口 (`/api/v1/competitor/core-info`)**
  - 提取：标题、高清大图、品牌及店铺链接、父体 ASIN、当前展示价、发货方式、上架时间。
- [x] **任务 1.3：竞品销售与BSR原子接口 (`/api/v1/competitor/sales-rank`)**
  - 提取：大类 BSR 实时排名、月预估销量 (件)、月预估销售额 ($)、日均出单预测。
- [x] **任务 1.4：竞品促销原子接口 (`/api/v1/competitor/promotions`)**
  - 提取：页面标价、Coupon 优惠券面额/类型、秒杀活动状态、券后实际到手价。
- [x] **任务 1.5：竞品评价动向原子接口 (`/api/v1/competitor/reviews`)**
  - 提取：当前评分星级 (如 4.3)、评论总数 (Ratings)、近 30 天新增评论数。
- [x] **任务 1.6：竞品流量词原子接口 (`/api/v1/competitor/traffic-keywords`)**
  - 已对接 `/v2/keyword-reverse/{站点}/{ASIN}/more`，字段解析就绪。
  - **双通道冗余（已解决）**：主通道「关键词反查」对本账号恒定返回空结果
    （`total=0, items=[]`，HTTP 仍是 200）。已排查确认**不是参数问题**——
    `station` 路径解析完全正常（US→`GLOBAL`、JP→`JAPAN`、DE→`GERMANY` 均正确回显），
    variation 接口也正常返回变体列表但每个变体 `total` 都是 0，
    根因是该试用账号 `valid-pay-status=false`，**套餐不含关键词反查权益**。
    故增加备通道 `/v2/aba/reverse/search/more`（出单词反查，含点击份额/转化份额），
    主通道空时自动降级，响应中 `source` 字段标明数据来源。换付费账号后主通道自动生效。
  - **实测**：B0CMJTSVRW → ABA 通道返回 82 个出单词，首词点击份额 31.11%。
- [x] **任务 1.7：竞品监控顶层聚合接口 (`/api/v1/competitor/monitor-summary`)**
  - 整合 1.2 ~ 1.6 的全部原子模块，一次性输出单 ASIN 的全维度监控数据。
  - 内置 180 秒缓存，避免聚合时重复拉取竞品反查页。

---

### 第二阶段：关键词挖掘与流量词反查板块 (`keywords`)

- [x] **任务 2.1：关键词挖掘与选词接口 (`/api/v1/keywords/research`)**
  - 对应网页版：`/v2/keyword-research`（服务端渲染表格，表头驱动解析）
  - 字段：关键词、中文翻译、月搜索量、日均搜索量、月购买量、购买率、展示量、点击量、
    增长率、同比增长、点击集中度、ABA 排名、货流值、PPC 建议竞价与区间、需供比、
    在售商品数、Top 商品均价/月销/评分。**已实测出真实数据。**
- [x] **任务 2.2：出单词反查 / ABA 搜索词接口 (`/api/v1/keywords/aba-reverse`)**
  - 已对接 `/v2/aba/reverse/search/more`，动态读取页面最新周表（ara_YYYYMMDD）与月表。
  - **已实测出真实数据**：B0CMJTSVRW → total=82，返回 32 条出单词（关键词、ABA 搜索频率排名、
    点击份额、转化份额、月搜索量）。注意用 Echo Dot 之类 ASIN 查会为空，
    并非接口问题而是该 ASIN 当期 ABA 无收录。
- [x] **任务 2.2b：关键词反查接口 (`/api/v1/keywords/reverse`)**
  - 输入 ASIN → 全量曝光关键词；**双通道自动降级**（主 `/v2/keyword-reverse`，空则切 ABA）。
  - 响应 `source` 标明实际来源，`notice` 说明降级原因与字段差异。
  - **实测**：B0CMJTSVRW → source=aba-reverse，total=82。
- [x] **任务 2.3：关键词收录检测接口 (`/api/v1/keywords/checker`)**
  - 网页版为两步式（POST 建任务拿 `flag` → 轮询 `result/{flag}`），且 `/v2/keyword-checker/*`
    子路由在本账号下直接 404，无法稳定抓取，故改为**反查命中判定**实现。
  - 判定逻辑：拉该 ASIN 全部曝光词 → 逐个比对传入关键词（精确 + 双向包含）→
    命中即「已收录」，并回填 ABA 排名/点击份额；每个词的依据写入 `evidence`。
  - **实测**：`wireless mics for iphone` 命中，`yoga mat` 未命中。

---

### 第三阶段：选产品与大盘选市场板块 (`product` & `market`)

- [x] **任务 3.1：产品库多维度选品接口 (`/api/v1/product/filter`)**
  - 对应网页版：`GET /v2/product-research/monthly`（**必须带 `/monthly` 后缀**）
  - **必须用 `nodeIdPath`**（冒号分隔的完整类目路径，如 `1055398:284507:...`），只传 `nodeId` 无效。
  - **`order.field` 是枚举值**：`total_units / total_amount / bsr_rank / price / rating / profit`。
    传非法值（如 `units`）服务端不报错、直接返回「暂无结果」空页 —— 这是最容易误判成"接口不通"的坑。
  - 筛选参数名已从表单实测校准：`minSales/maxSales`、`minAmount/maxAmount`、`minRanking/maxRanking`、
    `minReviews/maxReviews`、`minReviewRating/maxReviewRating`、`minProfit/maxProfit`、
    `minQuestions/maxQuestions`、`minVariations/maxVariations`、`minFba/maxFba`、
    `keywords/outOfKeywords`、`sellerType`、`sellerNations`、`bestSeller/newRelease`。
  - 解析：页面 `<tr>` 未嵌在 `<tbody>` 内，用 `parser.extract_rows_loose()` 正则容错，稳定 20~50 条。
  - **已实测出真实数据**：20 条商品，含毛利率/BSR 变化/留评率/上架时长等 20+ 字段。
- [x] **任务 3.2：细分市场分析接口 (`/api/v1/market/research`)**
  - 对应网页版：`/v2/market-research`
  - 输出：样本商品/品牌/卖家数、月总销量、月均销量、平均价格、平均评分与评分数、
    平均 BSR、FBA/AMZ/FBM 结构、商品/品牌/卖家集中度、新品数量与占比、商品总数、
    退货率与类目均值；**额外解析出平均毛利率、A+ 占比、中国卖家占比、
    新品平均价格/销量/评分、平均重量体积、搜索购买比**。**已实测出真实数据。**

---

### 第四阶段：常态化监控追踪看板 (`tracking`) —— 代码完成，**未验收** ⚠️

> 该板块 3 个接口的代码与路由已全部实现，但账号网页端没有任何监控对象，
> 无法按"真实数据验收"原则勾选。且复核时发现官网 `/v2/product-tracking`
> 有时返回的是关键词监控的列，已在服务层加表头健全性校验（表头不符直接返回 `notice` 拒绝解析）。

- [ ] **任务 4.1：产品动态监控接口 (`/api/v1/tracking/products`)**
  - 对应网页版：`/v2/product-tracking`
  - 功能：查询用户在网页端关注的 ASIN 实时变动（**新增/删除动作未实现**，涉及扣额度，应网页端确认）。
- [ ] **任务 4.2：关键词排名监控接口 (`/api/v1/tracking/keywords`)**
  - 对应网页版：`/v2/keyword-tracking`
  - 功能：监控目标 ASIN 在指定关键词下的日级别排位波动（**只读**）。
- [ ] **任务 4.3：店铺上新与竞店监控接口 (`/api/v1/tracking/stores`)**
  - 对应网页版：`/v2/store-tracking`
  - 功能：读取竞店最新上架 Listing 与动销情况（**只读**）。

---

### 第五阶段：实用算法工具板块 (`tools`)

- [x] **任务 5.1：销量预测计算器 (`/api/v1/tools/sales-estimator`)**
  - 实现方式调整：官网 `/v2/tools/sales-estimator` 底层接口有 Google reCAPTCHA 拦截，改为**本地 BSR 幂律模型**估算，零额度消耗、不受风控影响，参数（类目基准销量、弹性系数）可校准。
- [x] **任务 5.2：利润与 FBA 费用计算器 (`/api/v1/tools/profit-calculator`)**
  - 完整拆解：佣金/配送费/头程/仓储/广告/退货损耗/采购/其它，输出毛利、净利、ROI、保本售价。纯本地计算。

---

### 第六阶段：工程化交付与跨平台部署支撑

- [x] **任务 6.1：Docker 容器化镜像构建 (`Dockerfile` & `docker-compose.yml`)**
  - python:3.11-slim 基础镜像，`/app/data` 卷持久化 Cookie 与熔断状态，内置 HEALTHCHECK。
- [x] **任务 6.2：一键启动脚本 (`start.bat` / `start.sh`)**
  - Windows 双击自动建 venv、装依赖、校验配置后启动；Linux/macOS 脚本同能力。
- [x] **任务 6.3：接口限流保护与防封禁机制**
  - Cookie 7 天持久化、登录熔断（24h/3 次 + 30min 冷却）、2~4 秒拟人抖动、并发防重锁，全部已落地。
- [x] **任务 6.4：交付文档（`README.md`）**
  - 19 个接口清单、部署方式、配置说明、防封机制、**已知限制诚实说明**、逆向踩坑表。

---

## 📌 执行原则（给后续 AI 智能体的硬规则）

1. **先原子，后聚合**：新增任何功能时，严禁一开始做全量大接口，必须先将数据细分为原子接口，最后在 Facade 做聚合。
2. **强类型 Pydantic Schema**：每个接口都必须有对应的 Schema 文件，杜绝裸奔返回原始未经清洗的脏字典。
3. **真实端到端验证**：每个模块写完，必须用真实 ASIN 执行测试并校验返回结果，确认数据有效后才能勾选完成。
4. **零造假原则**：接口取不到数据时返回空列表 + `notice` 说明原因，**绝不用 mock 数据冒充真实结果**。
5. **禁止脚本各自登录**：所有测试与业务代码统一走 `SellerSpriteSession`，复用 `data/session_cookies.json`，否则会触发账号锁定。

---

## 📊 实施进度快照（2026-10-27 复核）

| 板块 | 进度 | 说明 |
|---|---|---|
| 1. 竞品监控 | 6/6 接口完成，**已验收** | traffic-keywords 采用双通道冗余，ABA 备通道出真实数据 |
| 2. 关键词挖掘 | 4/4 接口完成，**已验收** | reverse 双通道降级；checker 改为反查命中判定 |
| 3. 选品选市 | 2/2 接口完成，**已验收** | product/filter 已攻克（`/monthly` + `nodeIdPath` + 枚举排序字段） |
| 4. 监控追踪 | 3/3 接口编码完成，**未验收** ⚠️ | 只读设计；账号网页端无监控对象，尚未用真实数据验证；且发现官网 `product-tracking` 有时返回关键词监控的列，已加表头校验拒绝解析 |
| 5. 算法工具 | 2/2 完成 | 均为本地计算，零额度消耗 |
| 6. 工程化 | 4/4 完成 | Windows/Linux/Docker 均可一键启动 |
| （架构图里的 `user.py` 账号/额度板块） | **0/0 未开工** | 架构规范中列出，但任务清单里没有对应任务，实际也未实现 |

**⚠️ 当前唯一硬阻塞：账号凭证失效。**
2026-10-27 复核时，`192****0913` 登录被官网判定**密码错误**
（原文：`密码错误，如果连续【10】次密码错误，系统将锁定此账号！您已连续密码错误【2】次！`）。
系统已按设计熔断，未继续重试。需更换有效账号/密码后，才能验收板块 4 并复验其余接口。

**2026-10-27 修复的健壮性缺陷（比"缺功能"更危险）：**
1. 官网掉线时返回 **HTTP 200 + 登录页**（不是 302），旧逻辑把它当业务页解析 →
   空结果 → 对外报成「没有数据 / 会员额度不足」。已加 `is_login_html()` 识别并抛
   `SessionExpiredError`（503），与 429 限流语义区分。
2. `密码错误` 曾被误判为「账号已锁定」（只因文案里含"锁定"二字），提示方向错误。
3. 同一轮登录失败被重复计数两次，2 次尝试即顶到熔断阈值 4。

真实数据已验证的接口（2026-10-26，账号 `192****0913`，账号到期日 2026-10-31）：
- `competitor/monitor-summary?asin=B0CMJTSVRW` → BSR 5 / 月销 30305 / 月销额 $757,322 / 评分 4.3 / 评分数 9831
- `competitor/traffic-keywords?asin=B0CMJTSVRW` → ABA 通道 82 个出单词，首词点击份额 31.11%
- `keywords/research?keyword=yoga+mat` → yoga mat 月搜 1,147,222 / 购买率 2.52% / PPC $0.92 / 需供比 79.2
- `keywords/aba-reverse?asin=B0CMJTSVRW` → 82 个出单词，无线麦克风类词点击份额 9.09%
- `keywords/reverse?asin=B0CMJTSVRW` → source=aba-reverse，total=82
- `keywords/checker?asin=B0CMJTSVRW&keywords=wireless mics for iphone` → 命中
- `market/research` → Anti-Dust Plugs 月销 217,158 / 均价 $7.47 / 平均毛利率 53.28% / 中国卖家 91% / A+ 77% / 搜索购买比 11.6‰
- `product/filter?node_id_path=1055398:284507:289754:760384:289735:678496011` → 20 条商品；首位 B08SGPWY8Z / $12.23 / 月销 3404 / 毛利率 19% / BSR 1820
- `tools/profit-calculator` → 售价 $29.99 时净利 $10.86 / 净利率 36.21% / ROI 56.77% / 保本价 $15.11

---

## 🚧 计划边界之外：网页版还有哪些功能没转 API

上面 6 大板块是按"竞品监控 + 选品"这条业务主线裁剪过的，**不等于网页版全部功能**。
按官网 v3 模块清单对照，以下模块尚未纳入（可作为第二期）：

| 官网模块 | 功能 | 当前状态 |
|---|---|---|
| `keyword-miner` | 关键词挖掘（v3 版，按词根拓词） | 未做（v2 版 `keyword-research` 已做） |
| `aba-research` | ABA 数据研究 | 未做（仅做了按 ASIN 的出单词反查） |
| `competitor-lookup` | 竞品反查 / 竞品库（按类目批量找竞品） | 部分（只有单 ASIN 监控，无批量找竞品） |
| `ads-insights` | 广告洞察 | 未做 |
| `ai-review-analysis` / `review-analysis` | AI 评论分析 | 未做 |
| `branddb` | 全球品牌库 | 未做 |
| `keyword-comparison` | 关键词对比 | 未做 |
| `keyword-conversion-rate` | 关键词转化率 | 未做 |
| `keyword-store` / `product-store` | 词库 / 产品库（用户自建收藏） | 未做 |
| `promotion` | Deal / 促销查询 | 部分（只有单 ASIN 促销状态） |
| `real-time-bidding` | 实时竞价追踪 | 未做 |
| `relation-keyword` | 关联关键词 | 未做 |
| `patent` | 专利查询 | 未做 |
| `listing-builder` / `link-builder` | Listing 生成 / 链接生成 | 未做 |
| 监控的**新增/删除** | 追踪看板写入 | 未做（仅只读） |
| `user.py` 板块 | 账号信息、套餐额度、剩余次数 | 未做 |

