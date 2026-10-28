# 模块一：竞品监控 (Competitor Monitor) 字段与接口设计规范

在亚马逊运营和卖家精灵网页版的使用场景中，「竞品监控」通常包含以下三大核心层面的监控：
1. **基础 Listing 态势监控**（价格、BSR、库存/购物车、评分、变体）
2. **销售与销量表现监控**（月销量、日销量、销售额趋势、优惠券波动）
3. **流量与关键词位监控**（自然排名、广告排名、关联流量坑位、流量词总数）

---

## 一、核心输出字段清单 (Schema)

标准化输出模型：`CompetitorMonitorResponse`

### 1. 基础画像维度 (Product Core Info)
| 字段名 (Field) | 类型 | 说明与业务意义 | 网页版对应源 |
| :--- | :--- | :--- | :--- |
| `asin` | string | 目标商品 ASIN (如 `B0XXXXXXXX`) | 输入参数 |
| `parent_asin` | string | 父体 ASIN，用于分析多变体结构 | 产品详情 |
| `marketplace` | string | 站点代码 (US, UK, DE, JP 等) | 输入参数 |
| `title` | string | Listing 完整标题 (监控是否被篡改/优化) | 产品详情 |
| `brand` | string | 品牌名称 | 产品详情 |
| `brand_url` | string | 品牌店铺链接 | 产品详情 |
| `seller_name` | string | 当前 BuyBox 卖家名称 (自营 / FBA / FBM) | BuyBox 详情 |
| `seller_id` | string | 卖家 ID | BuyBox 详情 |
| `fulfillment_type` | string | 配送方式 (`FBA`, `FBM`, `AMZ` 自营) | BuyBox 详情 |
| `image_url` | string | 主图缩略图/高清图 URL | 产品详情 |
| `release_date` | string | 上架时间 (YYYY-MM-DD)，判断是否为新品 | 产品详情 |
| `category_path` | list[str] | 完整类目树路径 | 类目信息 |
| `weight_lbs` / `dimensions` | float/str | 重量与包装尺寸 (监控 FBA 费用变动风险) | 基础参数 |

---

### 2. 价格与促销监控维度 (Price & Promotion)
| 字段名 (Field) | 类型 | 说明与业务意义 | 监控预警作用 |
| :--- | :--- | :--- | :--- |
| `current_price` | float | 当前展示标价 / BuyBox 价格 | 价格波动、跟卖破价 |
| `original_price` | float | 划线原价 (List Price) | 折扣力度分析 |
| `coupon_value` | float | 当前优惠券面额 (如 $5 off 或 10% off) | 隐藏降价监控 |
| `coupon_type` | string | 优惠券类型 (`PERCENT` 或 `AMOUNT`) | 促销打法跟踪 |
| `deal_type` | string | 当前秒杀活动状态 (None, LD, 7DD, Prime专享) | 竞品大促异动 |
| `net_price` | float | 真实到手价 (`current_price` - 实际抵扣) | 真实价格对比 |

---

### 3. 销售与排名监控维度 (Sales & Rank Dynamics)
| 字段名 (Field) | 类型 | 说明与业务意义 | 网页版对应源 |
| :--- | :--- | :--- | :--- |
| `bsr_main_rank` | int | 大类实时 BSR 排名 | Keepa / 实时抓取 |
| `bsr_main_category` | string | 大类名称 | 详情页 |
| `bsr_sub_rank` | int | 核心小类实时 BSR 排名 | 节点排名 |
| `bsr_sub_category` | string | 小类节点名称 | 节点排名 |
| `est_monthly_sales` | int | 卖家精灵预估月销量 (单位: 件) | 销量预测算法 |
| `est_monthly_revenue` | float | 卖家精灵预估月销售额 (单位: 当地货币) | 营收预测算法 |
| `est_daily_sales` | int | 预估近期日均销量 | 算法平滑值 |
| `rating` | float | 评分星级 (如 4.3) | 口碑评分预警 |
| `ratings_count` | int | 评论总数 (Rating/Review 数) | 增评速度/掉评预警 |

---

### 4. 流量结构与关键词渗透 (Traffic & Keywords)
| 字段名 (Field) | 类型 | 说明与业务意义 | 网页版对应源 |
| :--- | :--- | :--- | :--- |
| `traffic_keywords_count` | int | 有流量排名的关键词总数 | 流量词反查模块 |
| `organic_keywords_count` | int | 自然排名进前3页的关键词数 | 流量结构分析 |
| `sponsored_keywords_count`| int | 投放广告进前3页的关键词数 | 广告覆盖力度 |
| `organic_traffic_ratio` | float | 自然流量占比 (0.0 ~ 1.0) | 流量健康度 |
| `sponsored_traffic_ratio` | float | 广告流量占比 (0.0 ~ 1.0) | 广告依赖度 |
| `top_keywords_snapshot` | list[dict] | 核心流量词快照 (Top 10-20 词)：词、自然位、广告位、周/月搜量 | 关键词监控明细 |

---

### 5. 变体与库存监控 (Variants & Inventory)
| 字段名 (Field) | 类型 | 说明与业务意义 | 网页版对应源 |
| :--- | :--- | :--- | :--- |
| `variant_count` | int | 总变体数量 | 变体分析 |
| `is_best_variant` | bool | 是否为主卖/出单主力变体 | 变体销量占比 |
| `variant_sales_share` | float | 该子体占全父体的销量比例 (如 0.45 = 45%) | 变体销量推算 |
| `stock_status` | string | 库存状态 (`IN_STOCK`, `LOW_STOCK`, `OOS`) | 断货监控 |

---

## 二、REST API 接口设计

### 1. 单 ASIN 实时/快照监控详情
- **Method**: `GET` / `POST`
- **Path**: `/api/v1/competitor/asin-monitor`
- **Request Body**:
```json
{
  "marketplace": "US",
  "asin": "B0CMJTSVRW",
  "include_traffic": true,
  "include_variants": false
}
```

### 2. 批量 ASIN 监控矩阵 (Batch Monitor)
- **Method**: `POST`
- **Path**: `/api/v1/competitor/batch-monitor`
- **Request Body**:
```json
{
  "marketplace": "US",
  "asins": ["B0CMJTSVRW", "B09WXXXXXX", "B08YYYYYYY"]
}
```

### 3. 历史趋势数据提取 (Trend / Keepa-like Timeline)
- **Method**: `GET`
- **Path**: `/api/v1/competitor/history-trend`
- **Query Params**: `marketplace=US&asin=B0CMJTSVRW&days=30`
- **Return**: 包含日期维度的 `date`, `price`, `bsr`, `sales_est`, `ratings_count` 数组。
