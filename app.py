
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

import pandas as pd
import streamlit as st


# ==============================
# 1. 页面基本配置
# ==============================

st.set_page_config(
    page_title="SmartFinance CRM",
    page_icon="💰",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSET_DIR = BASE_DIR / "assets"

CUSTOMER_FILE = DATA_DIR / "customers.csv"
PRODUCT_FILE = DATA_DIR / "products.csv"
TRANSACTION_FILE = DATA_DIR / "transactions.csv"
ABNORMAL_FILE = DATA_DIR / "abnormal_customers.csv"


# ==============================
# 2. 初始化模拟数据
# ==============================

RISK_SCORE = {
    "低风险": 1,
    "中风险": 3,
    "高风险": 5
}


# 模拟订单模板：(重复次数, 该订单购买的商品)。同一客户同一天的商品构成一个订单。
SAMPLE_BASKETS = [
    (12, ["P001", "P003"]),
    (9, ["P002", "P004"]),
    (8, ["P005", "P007"]),
    (6, ["P003", "P007"]),
    (5, ["P006"]),
    (6, ["P008"]),
    (4, ["P009", "P010"]),
    (5, ["P002", "P008"]),
    (4, ["P001", "P009"]),
    (3, ["P010"]),
    (3, ["P004"]),
]

ABNORMAL_COLUMNS = [
    "customer_id",
    "age",
    "income",
    "risk_level",
    "min_distance",
    "best_product",
    "created_at"
]


def build_sample_transactions(products):
    """按订单模板生成模拟购买记录"""

    min_amount = dict(zip(products["product_id"], products["min_amount"]))
    customer_ids = [f"C{index:03d}" for index in range(1, 16)]

    rows = []
    basket_no = 0
    txn_no = 1
    base_date = pd.Timestamp("2026-09-01")

    for repeat, basket in SAMPLE_BASKETS:
        for _ in range(repeat):
            customer_id = customer_ids[basket_no % len(customer_ids)]
            buy_date = (
                base_date + pd.Timedelta(days=basket_no)
            ).date().isoformat()

            for product_id in basket:
                rows.append([
                    f"T{txn_no:04d}",
                    customer_id,
                    product_id,
                    buy_date,
                    int(min_amount[product_id])
                ])
                txn_no += 1

            basket_no += 1

    return pd.DataFrame(rows, columns=[
        "txn_id",
        "customer_id",
        "product_id",
        "buy_date",
        "amount"
    ])


def create_sample_data():
    """当CSV文件不存在时，自动生成模拟数据。"""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CUSTOMER_FILE.exists():
        customers = pd.DataFrame([
            ["C001", "客户001", 25, 80000, "低风险"],
            ["C002", "客户002", 28, 100000, "低风险"],
            ["C003", "客户003", 35, 120000, "低风险"],
            ["C004", "客户004", 30, 150000, "中风险"],
            ["C005", "客户005", 32, 180000, "中风险"],
            ["C006", "客户006", 38, 200000, "中风险"],
            ["C007", "客户007", 42, 250000, "中风险"],
            ["C008", "客户008", 26, 160000, "中风险"],
            ["C009", "客户009", 40, 300000, "高风险"],
            ["C010", "客户010", 45, 350000, "高风险"],
            ["C011", "客户011", 29, 220000, "高风险"],
            ["C012", "客户012", 50, 400000, "高风险"],
            ["C013", "客户013", 33, 130000, "低风险"],
            ["C014", "客户014", 37, 240000, "中风险"],
            ["C015", "客户015", 48, 320000, "高风险"],
        ], columns=[
            "customer_id",
            "name",
            "age",
            "income",
            "risk_level"
        ])

        customers.to_csv(
            CUSTOMER_FILE,
            index=False,
            encoding="utf-8-sig"
        )

    if not PRODUCT_FILE.exists():
        products = pd.DataFrame([
            ["P001", "稳健理财A", "银行理财", "低风险", 1, 25, 70, 50000, 80000, 200000, "assets/P001.png"],
            ["P002", "指数基金B", "基金", "中风险", 3, 22, 65, 10000, 120000, 300000, "assets/P002.png"],
            ["P003", "黄金积存C", "贵金属", "中风险", 3, 18, 75, 1000, 60000, 250000, "assets/P003.png"],
            ["P004", "成长基金D", "基金", "高风险", 5, 25, 55, 10000, 150000, 400000, "assets/P004.png"],
            ["P005", "短债基金E", "基金", "低风险", 1, 22, 65, 1000, 50000, 180000, "assets/P005.png"],
            ["P006", "养老理财F", "银行理财", "低风险", 1, 30, 75, 10000, 80000, 260000, "assets/P006.png"],
            ["P007", "黄金定投G", "贵金属", "中风险", 3, 20, 70, 500, 60000, 250000, "assets/P007.png"],
            ["P008", "混合基金H", "基金", "中风险", 3, 25, 60, 10000, 100000, 350000, "assets/P008.png"],
            ["P009", "定期寿险I", "保险", "低风险", 1, 25, 65, 2000, 70000, 300000, "assets/P009.png"],
            ["P010", "量化对冲J", "基金", "高风险", 5, 30, 60, 50000, 200000, 500000, "assets/P010.png"],
        ], columns=[
            "product_id",
            "product_name",
            "product_type",
            "risk_level",
            "risk_score",
            "age_min",
            "age_max",
            "min_amount",
            "income_min",
            "income_max",
            "image"
        ])

        products.to_csv(
            PRODUCT_FILE,
            index=False,
            encoding="utf-8-sig"
        )

    if not TRANSACTION_FILE.exists():
        build_sample_transactions(products).to_csv(
            TRANSACTION_FILE,
            index=False,
            encoding="utf-8-sig"
        )

    if not ABNORMAL_FILE.exists():
        pd.DataFrame(columns=ABNORMAL_COLUMNS).to_csv(
            ABNORMAL_FILE,
            index=False,
            encoding="utf-8-sig"
        )


# ==============================
# 3. 数据读取与检查
# ==============================

@st.cache_data
def load_data():
    """读取客户数据和金融产品数据。"""

    customers = pd.read_csv(
        CUSTOMER_FILE,
        encoding="utf-8-sig"
    )

    products = pd.read_csv(
        PRODUCT_FILE,
        encoding="utf-8-sig"
    )

    transactions = pd.read_csv(
        TRANSACTION_FILE,
        encoding="utf-8-sig"
    )

    customer_columns = {
        "customer_id", "name", "age", "income", "risk_level"
    }

    product_columns = {
        "product_id", "product_name", "product_type",
        "risk_level", "risk_score",
        "age_min", "age_max", "min_amount",
        "income_min", "income_max", "image"
    }

    transaction_columns = {
        "txn_id", "customer_id", "product_id", "buy_date", "amount"
    }

    if not customer_columns.issubset(customers.columns):
        raise ValueError("customers.csv 缺少必要字段")

    if not product_columns.issubset(products.columns):
        raise ValueError("products.csv 缺少必要字段")

    if customers.empty or products.empty:
        raise ValueError("客户数据或产品数据为空")

    if not customers["risk_level"].isin(RISK_SCORE).all():
        raise ValueError("客户风险等级只能为低风险、中风险或高风险")

    if not pd.to_numeric(customers["age"], errors="coerce").notna().all():
        raise ValueError("客户年龄数据存在无效值")

    if not pd.to_numeric(customers["income"], errors="coerce").notna().all():
        raise ValueError("客户收入数据存在无效值")

    products["risk_score"] = pd.to_numeric(
        products["risk_score"], errors="coerce"
    )

    if products["risk_score"].isna().any():
        raise ValueError("产品风险评分存在无效值")

    for column in ("age_min", "age_max", "min_amount", "income_min", "income_max"):
        products[column] = pd.to_numeric(products[column], errors="coerce")

        if products[column].isna().any():
            raise ValueError(f"产品 {column} 存在无效值")

    if not (products["age_min"] < products["age_max"]).all():
        raise ValueError("产品年龄区间设置不合理")

    if not (products["income_min"] < products["income_max"]).all():
        raise ValueError("产品收入区间设置不合理")

    if not transaction_columns.issubset(transactions.columns):
        raise ValueError("transactions.csv 缺少必要字段")

    if not transactions["product_id"].isin(products["product_id"]).all():
        raise ValueError("购买记录中存在未知产品编号")

    return customers, products, transactions


# ==============================
# 3.5 距离函数（最近邻方法）
# ==============================

# 分母使用固定参照区间，避免新客户的极端值改变历史客户的距离与排名
AGE_MIN_REF, AGE_MAX_REF = 18, 80
AGE_DENOM = AGE_MAX_REF - AGE_MIN_REF
INCOME_SPAN_REF = 300_000
RISK_MAX_DIFF = 4

# 区间内的距离上限：区间内最高 0.5，区间外再从 0.5 累加到 1.0
IN_RANGE_MAX = 0.5


def distance_in_range(value, low, high, span_ref):
    """
    区间型属性的归一化距离。

    区间内：按偏离区间中点的相对位置取 0 到 IN_RANGE_MAX；
    区间外：从 IN_RANGE_MAX 起按超出量叠加到 1.0。
    """

    center = (low + high) / 2
    half = max((high - low) / 2, 1e-9)

    if value < low:
        gap = low - value
    elif value > high:
        gap = value - high
    else:
        gap = 0

    inner = min(abs(value - center) / half, 1.0) * IN_RANGE_MAX
    outer = min(gap / span_ref, 1.0) * (1 - IN_RANGE_MAX)

    return min(inner + outer, 1.0)


def distance_age(age, age_min, age_max):
    """
    年龄距离：越靠近适龄区间中点越接近 0，超出区间后继续增大。

    区间内不再恒为 0：中点处为 0，区间端点处为 0.5；
    区间外从 0.5 起按偏离量继续增长，最多到 1.0。
    """

    return distance_in_range(age, age_min, age_max, AGE_DENOM)


def distance_income(income, income_min, income_max, min_amount):
    """
    收入距离：越靠近产品目标收入区间中点越接近 0，区间外继续增大。

    收入低于起投金额时直接记为 1.0，表示不满足参与门槛。
    """

    if income < min_amount:
        return 1.0

    return distance_in_range(income, income_min, income_max, INCOME_SPAN_REF)


def distance_risk(customer_score, product_score, scale=1 / RISK_MAX_DIFF):
    """
    风险距离：|Δ| * scale，截断到 1.0。

    scale=0.25：等价于 |Δ| / RISK_MAX_DIFF，用于多维模式
    scale=0.20：等价于原有公式的等效距离，用于单维模式
    """

    return min(abs(customer_score - product_score) * scale, 1.0)


# ==============================
# 3.6 算法配置（统一契约）
# ==============================

# 内部一律使用 [0,1] 距离，百分制只在出口换算一次
ALGORITHM_CONFIG = {
    # 原有算法：单维风险匹配，等价于 100 - 20 * |Δ|
    "risk": {
        "weights": {"risk": 1.0, "income": 0.0, "age": 0.0},
        "risk_scale": 0.20
    },
    # 新增算法：三维加权距离
    "multi": {
        "weights": {"risk": 0.60, "income": 0.25, "age": 0.15},
        "risk_scale": 0.25
    }
}

# 任何算法必须返回同一列集合
RESULT_COLUMNS = [
    "product_id",
    "product_name",
    "product_type",
    "risk_level",
    "score",
    "distance",
    "d_risk",
    "d_income",
    "d_age",
    "reason"
]


# ==============================
# 3.7 关联算法参数（Apriori 简化版）
# ==============================

# 支持度、置信度、兴趣度的筛选下限（课件要求：置信度大于设定值或兴趣度大于1）
MIN_SUPPORT = 0.06
MIN_CONFIDENCE = 0.5
MIN_LIFT = 1.0

# 最近邻：最小距离超过该值，视为样例表覆盖不到。
# 课件举例 0.6；在默认权重（风险 0.6 / 收入 0.25 / 年龄 0.15）下，
# 三个维度即使全部拉到最大，组合距离也只有 1.0，而风险接近的产品实际最小距离
# 上限约 0.55，因此取 0.5 才有区分度。
DISTANCE_THRESHOLD = 0.5
TOP_N = 3


def build_baskets(transactions):
    """把购买记录按「同一客户同一天」聚合成订单。"""

    return [
        set(group["product_id"])
        for _, group in transactions.groupby(["customer_id", "buy_date"])
    ]


def mine_rules(
    transactions,
    min_support=MIN_SUPPORT,
    min_confidence=MIN_CONFIDENCE,
    min_lift=MIN_LIFT
):
    """
    简化版 Apriori：

    1. 先求频繁 1-项集；
    2. 只求频繁 2-项集（课件要求只关注两个商品之间的关联）；
    3. 每个 2-项集生成两条规则，用置信度与兴趣度筛选。
    """

    columns = ["antecedent", "consequent", "support", "confidence", "lift"]

    baskets = build_baskets(transactions)
    total = len(baskets)

    if total == 0:
        return pd.DataFrame(columns=columns)

    # 第一步：频繁 1-项集
    single_counter = Counter()

    for items in baskets:
        single_counter.update(items)

    frequent_single = {
        item: count / total
        for item, count in single_counter.items()
        if count / total >= min_support
    }

    # 第二步：频繁 2-项集
    pair_counter = Counter()

    for items in baskets:
        for pair in combinations(sorted(items), 2):
            pair_counter[pair] += 1

    rows = []

    for (left, right), count in pair_counter.items():

        support = count / total

        if support < min_support:
            continue

        if left not in frequent_single or right not in frequent_single:
            continue

        # 第三步：每个 2-项集生成两条规则
        for antecedent, consequent in ((left, right), (right, left)):

            confidence = count / single_counter[antecedent]
            lift = confidence / frequent_single[consequent]

            if confidence >= min_confidence and lift > min_lift:
                rows.append([
                    antecedent,
                    consequent,
                    support,
                    confidence,
                    lift
                ])

    rules = pd.DataFrame(rows, columns=columns)

    if rules.empty:
        return rules

    return rules.sort_values(
        ["lift", "confidence"], ascending=False
    ).reset_index(drop=True)


def recommend_by_rules(rules, purchased_ids, top_n=TOP_N):
    """给定已购买的商品，按规则推导「可能还想买」。"""

    columns = ["product_id", "confidence", "lift", "support"]

    if rules.empty or not purchased_ids:
        return pd.DataFrame(columns=columns)

    purchased = set(purchased_ids)

    hit = rules[
        rules["antecedent"].isin(purchased)
        & ~rules["consequent"].isin(purchased)
    ]

    if hit.empty:
        return pd.DataFrame(columns=columns)

    aggregated = (
        hit.groupby("consequent")
        .agg(
            confidence=("confidence", "max"),
            lift=("lift", "max"),
            support=("support", "max")
        )
        .reset_index()
        .rename(columns={"consequent": "product_id"})
        .sort_values(["confidence", "lift"], ascending=False)
    )

    return aggregated.head(top_n).reset_index(drop=True)


def hot_products(transactions, top_n=TOP_N):
    """按购买次数取热门商品（冷启动与异常客户的兜底推荐）。"""

    if transactions.empty:
        return pd.DataFrame(columns=["product_id", "buy_count"])

    counts = transactions["product_id"].value_counts().head(top_n)

    return counts.rename_axis("product_id").reset_index(name="buy_count")


def min_distance_of(recommendation):
    """最近邻：客户与全部产品中的最小距离及对应产品。"""

    row = recommendation.loc[recommendation["distance"].idxmin()]

    return float(row["distance"]), row["product_name"]


# ==============================
# 4. 产品推荐算法（统一管线）
# ==============================

def build_reason(weights, row):
    """由各维度贡献度生成理由，保证解释与排序依据同源。"""

    contributions = {
        key: weights[key] * row[f"d_{key}"] ** 2
        for key in ("risk", "income", "age")
    }

    active = [key for key in contributions if weights[key] > 0]
    total = sum(contributions[key] for key in active)

    if total == 0:
        return "产品各项属性与客户情况完全匹配。"

    dominant = max(active, key=lambda key: contributions[key])
    ratio = contributions[dominant] / total
    gap = row[f"d_{dominant}"]

    label = {
        "risk": "风险等级",
        "income": "资金门槛",
        "age": "适龄区间"
    }[dominant]

    if gap <= 0.05:
        return f"{label}与客户情况高度匹配，为主要推荐依据。"

    if ratio >= 0.6:
        return f"主要差异来自{label}，其余维度匹配较好。"

    return f"多个维度存在一定差异，其中{label}影响最大。"


def score_products(customer, products, config):
    """
    统一评分入口：任一算法都通过此函数产出同一结构。

    config 包含 weights（各维度权重，和为 1）与 risk_scale。
    返回列集合固定为 RESULT_COLUMNS。
    """

    weights = config["weights"]
    customer_score = RISK_SCORE[customer["risk_level"]]

    rows = []

    for _, product in products.iterrows():

        d_risk = distance_risk(
            customer_score,
            product["risk_score"],
            config["risk_scale"]
        )

        d_income = distance_income(
            float(customer["income"]),
            float(product["income_min"]),
            float(product["income_max"]),
            float(product["min_amount"])
        )

        d_age = distance_age(
            int(customer["age"]),
            int(product["age_min"]),
            int(product["age_max"])
        )

        total = sum(
            weights[key] * value ** 2
            for key, value in (
                ("risk", d_risk),
                ("income", d_income),
                ("age", d_age)
            )
        )

        distance = min(math.sqrt(total), 1.0)

        rows.append({
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "product_type": product["product_type"],
            "risk_level": product["risk_level"],
            "distance": distance,
            "score": 100.0 * (1.0 - distance),
            "d_risk": d_risk,
            "d_income": d_income,
            "d_age": d_age
        })

    scored = pd.DataFrame(rows)

    scored["reason"] = [
        build_reason(weights, row)
        for _, row in scored.iterrows()
    ]

    return scored[RESULT_COLUMNS]


def rank_products(scored):
    """统一排序出口：一律按 score 降序，同分按名称升序。"""

    ranked = scored.sort_values(
        by=["score", "product_name"],
        ascending=[False, True]
    ).reset_index(drop=True)

    ranked.insert(0, "ranking", range(1, len(ranked) + 1))

    return ranked


def recommend_products(customer, products, weights=None, sort_by="risk"):
    """
    保持原有函数签名，内部改走统一管线。

    sort_by="risk"  : 单维风险匹配（原有行为，默认）
    sort_by="multi" : 三维加权距离
    """

    config = dict(ALGORITHM_CONFIG[sort_by])

    if weights is not None:
        config["weights"] = weights

    return rank_products(score_products(customer, products, config))


# ==============================
# 4.9 数据回写（购买记录 / 异常客户记录）
# ==============================

def append_purchase(customer_id, product_id, amount):
    """把一次购买写回 transactions.csv（同一客户同一天算一个订单）。"""

    transactions = pd.read_csv(TRANSACTION_FILE, encoding="utf-8-sig")

    existing = pd.to_numeric(
        transactions["txn_id"].str.lstrip("T"), errors="coerce"
    ).fillna(0)

    row = pd.DataFrame([{
        "txn_id": f"T{int(existing.max()) + 1:04d}",
        "customer_id": customer_id,
        "product_id": product_id,
        "buy_date": pd.Timestamp.today().date().isoformat(),
        "amount": amount
    }])

    row.to_csv(
        TRANSACTION_FILE,
        mode="a",
        header=False,
        index=False,
        encoding="utf-8-sig"
    )


def record_abnormal(customer, min_distance, best_product):
    """把「样例表覆盖不到」的客户写入异常客户记录表。"""

    row = pd.DataFrame([{
        "customer_id": customer["customer_id"],
        "age": int(customer["age"]),
        "income": float(customer["income"]),
        "risk_level": customer["risk_level"],
        "min_distance": round(min_distance, 4),
        "best_product": best_product,
        "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }])

    row.to_csv(
        ABNORMAL_FILE,
        mode="a",
        header=False,
        index=False,
        encoding="utf-8-sig"
    )


def load_abnormal():
    """读取异常客户记录表。"""

    if not ABNORMAL_FILE.exists():
        return pd.DataFrame(columns=ABNORMAL_COLUMNS)

    return pd.read_csv(ABNORMAL_FILE, encoding="utf-8-sig")


# ==============================
# 5. 页面标题
# ==============================

st.title("💰 SmartFinance CRM")
st.subheader("金融产品智能推荐系统")

st.markdown(
    """
    本系统同时演示两种推荐算法：

    - 关联算法（Apriori）：根据「买了什么」推荐「还可能想买什么」；
    - 最近邻算法：根据客户年龄、收入、风险偏好推荐匹配度最高的产品。
    """
)

st.divider()


# ==============================
# 6. 加载数据
# ==============================

try:
    create_sample_data()
    customers, products, transactions = load_data()

except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"数据加载失败：{error}")
    st.stop()


# ==============================
# 7. 客户选择与信息展示
# ==============================

st.header("一、客户信息管理")

customer_source = st.radio(
    "客户来源",
    options=["选择已有客户", "输入新客户"],
    horizontal=True
)

if customer_source == "选择已有客户":

    customer_options = {
        f"{row['customer_id']} - {row['name']}": row["customer_id"]
        for _, row in customers.iterrows()
    }

    selected_customer = st.selectbox(
        "请选择需要分析的客户",
        options=list(customer_options.keys())
    )

    customer_id = customer_options[selected_customer]

    customer = customers.loc[
        customers["customer_id"] == customer_id
    ].iloc[0]

else:

    # 新客户不写入 CSV，仅构造与 CSV 行同构的 Series
    with st.form("new_customer_form"):
        col_a, col_b, col_c = st.columns(3)

        new_age = col_a.number_input(
            "客户年龄",
            min_value=18,
            max_value=80,
            value=30
        )

        new_income = col_b.number_input(
            "年收入（万元）",
            min_value=0.0,
            max_value=500.0,
            value=15.0,
            step=1.0
        )

        new_risk = col_c.selectbox(
            "风险偏好",
            options=list(RISK_SCORE.keys())
        )

        st.form_submit_button("生成推荐")

    customer = pd.Series({
        "customer_id": "NEW",
        "name": "新客户",
        "age": int(new_age),
        "income": float(new_income) * 10000,
        "risk_level": new_risk
    })

col1, col2, col3, col4 = st.columns(4)

col1.metric("客户编号", customer["customer_id"])
col2.metric("客户年龄", f"{customer['age']} 岁")
col3.metric("年收入", f"{customer['income'] / 10000:.1f} 万元")
col4.metric("风险偏好", customer["risk_level"])

st.divider()


# ==============================
# 8. 金融产品展示
# ==============================

st.header("二、金融产品货架")

st.caption(
    "卡片展示产品图片与基本信息；点击「购买」会生成一条购买记录，供关联算法使用。"
)

product_lookup = products.set_index("product_id")

for start in range(0, len(products), 4):

    shelf_columns = st.columns(4)

    for column, (_, product) in zip(
        shelf_columns, products.iloc[start:start + 4].iterrows()
    ):
        with column:

            image_path = BASE_DIR / product["image"]

            if image_path.exists():
                st.image(str(image_path), use_container_width=True)

            # use_container_width 在新旧版本 Streamlit 上都可用
            st.markdown(f"**{product['product_name']}**")
            st.caption(
                f"{product['product_type']} ｜ {product['risk_level']} ｜ "
                f"风险评分 {product['risk_score']}"
            )
            st.caption(
                f"起投 {int(product['min_amount']):,} 元 ｜ "
                f"适合 {int(product['age_min'])}–{int(product['age_max'])} 岁"
            )

            if st.button(
                "购买",
                key=f"buy_{product['product_id']}",
                use_container_width=True
            ):
                append_purchase(
                    customer["customer_id"],
                    product["product_id"],
                    float(product["min_amount"])
                )
                load_data.clear()
                st.rerun()


def render_product_card(column, product_id, extra_lines=()):
    """在列中渲染一张产品卡片（图片 + 名称 + 类型风险 + 附加说明）。"""

    product = product_lookup.loc[product_id]
    image_path = BASE_DIR / product["image"]

    with column:

        if image_path.exists():
            st.image(str(image_path), use_container_width=True)

        st.markdown(f"**{product['product_name']}**")
        st.caption(f"{product['product_type']} ｜ {product['risk_level']}")

        for line in extra_lines:
            st.caption(line)


st.divider()


# ==============================
# 9. 智能推荐
# ==============================

st.header("三、智能产品推荐")

tab_assoc, tab_neighbor = st.tabs([
    "① 买了还想买（关联算法）",
    "② 适合你的产品（最近邻算法）"
])

# 最近一次订单 = 同一客户同一天的商品集合
customer_orders = transactions[
    transactions["customer_id"] == customer["customer_id"]
]

if customer_orders.empty:
    latest_basket = customer_orders
else:
    latest_date = customer_orders["buy_date"].max()
    latest_basket = customer_orders[
        customer_orders["buy_date"] == latest_date
    ]

rules = mine_rules(transactions)


# ---------- ① 关联算法 ----------

with tab_assoc:

    st.caption(
        f"共 {len(build_baskets(transactions))} 个订单，"
        f"规则库 {len(rules)} 条（支持度 ≥ {MIN_SUPPORT}，"
        f"置信度 ≥ {MIN_CONFIDENCE}，兴趣度 > {MIN_LIFT}）"
    )

    if latest_basket.empty:

        st.info(
            "当前客户还没有购买记录。请先在「二、金融产品货架」点击「购买」，"
            "或先看看下面的热门商品。"
        )

        assoc_result = pd.DataFrame(
            columns=["product_id", "confidence", "lift", "support"]
        )

    else:

        # 同一客户同一天重复购买同一产品时，订单文案只保留一次
        purchased_ids = list(dict.fromkeys(latest_basket["product_id"]))

        st.markdown(
            "当前订单："
            + "、".join(
                product_lookup.loc[item, "product_name"]
                for item in purchased_ids
            )
        )

        assoc_result = recommend_by_rules(rules, purchased_ids)

    if assoc_result.empty:

        st.info("没有满足兴趣度要求的关联规则，先推荐当前热门商品。")

        fallback = hot_products(transactions)
        # 固定 4 列布局，推荐结果不足 4 个时卡片也不会被拉宽变形
        fallback_columns = st.columns(4)

        for column, (_, item) in zip(fallback_columns, fallback.iterrows()):
            render_product_card(
                column,
                item["product_id"],
                [f"近期购买 {int(item['buy_count'])} 次"]
            )

    else:

        st.subheader("您可能还想同时购买")

        result_columns = st.columns(max(len(assoc_result), 4))

        for column, (_, item) in zip(result_columns, assoc_result.iterrows()):
            render_product_card(
                column,
                item["product_id"],
                [
                    f"置信度 {item['confidence']:.2f}",
                    f"兴趣度 {item['lift']:.2f}",
                    f"支持度 {item['support']:.2f}"
                ]
            )

    with st.expander("查看关联规则明细"):

        rule_view = rules.rename(columns={
            "antecedent": "前项（已购买）",
            "consequent": "后项（推荐）",
            "support": "支持度",
            "confidence": "置信度",
            "lift": "兴趣度"
        })

        st.dataframe(rule_view, use_container_width=True, hide_index=True)


# ---------- ② 最近邻算法 ----------

with tab_neighbor:

    with st.expander("匹配参数设置", expanded=False):

        sort_by = st.radio(
            "排序依据",
            options=["风险匹配分（原有）", "综合匹配分（多维距离）"],
            horizontal=True
        )

        if sort_by.startswith("综合"):

            w_risk = st.slider("风险权重", 0.0, 1.0, 0.60, 0.05)
            w_income = st.slider("收入权重", 0.0, 1.0, 0.25, 0.05)
            w_age = st.slider("年龄权重", 0.0, 1.0, 0.15, 0.05)

            weight_sum = w_risk + w_income + w_age

            if weight_sum == 0:
                st.warning("权重之和不能为 0，已回退到风险匹配分排序。")
                sort_mode, weights = "risk", None
            else:
                # 归一化，保证三者之和为 1
                weights = {
                    "risk": w_risk / weight_sum,
                    "income": w_income / weight_sum,
                    "age": w_age / weight_sum
                }
                sort_mode = "multi"

        else:
            sort_mode, weights = "risk", None

    recommendation = recommend_products(
        customer,
        products,
        weights=weights,
        sort_by=sort_mode
    )

    st.markdown(
        f"当前分析客户：**{customer['name']}**，"
        f"风险偏好：**{customer['risk_level']}**"
    )

    best_product = recommendation.iloc[0]

    st.success(
        f"首选推荐产品：{best_product['product_name']} "
        f"（匹配分数：{best_product['score']:.0f}）"
    )

    # 仅提示，不改变推荐结果
    if best_product["risk_level"] != customer["risk_level"]:
        st.warning(
            "注意：首选推荐产品的风险等级与客户风险偏好不一致，"
            "按投资者适当性要求不建议主动推介，请谨慎参考。"
        )

    st.subheader("产品推荐排名")

    display_columns = [
        "ranking",
        "product_name",
        "product_type",
        "risk_level",
        "score",
        "reason"
    ]

    display_data = recommendation[display_columns].rename(
        columns={
            "ranking": "推荐排名",
            "product_name": "产品名称",
            "product_type": "产品类型",
            "risk_level": "风险等级",
            "score": "匹配分数",
            "reason": "推荐理由"
        }
    )

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )


st.divider()


# ==============================
# 10. 推荐结果分析
# ==============================

st.header("四、推荐结果分析")

col1, col2 = st.columns(2)

with col1:
    st.subheader("匹配分数分析")

    chart_data = recommendation.set_index(
        "product_name"
    )[["score"]]

    st.bar_chart(chart_data)

with col2:
    st.subheader("推荐结果说明")

    st.write(f"客户姓名：{customer['name']}")
    st.write(f"客户风险偏好：{customer['risk_level']}")
    st.write(f"首选推荐：{best_product['product_name']}")
    st.write(f"匹配分数：{best_product['score']:.0f}")

    st.info(
        best_product["reason"]
    )

with st.expander("查看分维度距离明细"):
    st.caption(
        "归一化距离：0 表示完全匹配，1 表示差异最大。"
        "综合分由加权欧氏距离换算而来。"
    )

    detail = recommendation[[
        "product_name", "d_risk", "d_income", "d_age", "score"
    ]].rename(columns={
        "product_name": "产品名称",
        "d_risk": "风险距离",
        "d_income": "收入距离",
        "d_age": "年龄距离",
        "score": "匹配分数"
    })

    st.dataframe(
        detail,
        use_container_width=True,
        hide_index=True
    )


# 最近邻的异常分支：最小距离超过阈值 → 写入异常客户记录表 + 改推热门商品
# 无论页面当前用哪种排序依据，都用默认权重的三维综合距离做判定
check_recommendation = recommend_products(customer, products, sort_by="multi")
min_distance, nearest_product = min_distance_of(check_recommendation)

if min_distance > DISTANCE_THRESHOLD:

    st.warning(
        f"该客户与全部产品的最小距离为 {min_distance:.2f}，超过阈值 "
        f"{DISTANCE_THRESHOLD}：样例表覆盖不到该客户，已作为新样例的"
        f"备选值写入异常客户记录表，本次改推热门商品。"
    )

    guard_key = f"abnormal::{customer['customer_id']}::{min_distance:.4f}"

    if guard_key not in st.session_state:
        record_abnormal(customer, min_distance, nearest_product)
        st.session_state[guard_key] = True

    st.subheader("热门商品（兜底推荐）")

    fallback = hot_products(transactions)
    fallback_columns = st.columns(max(len(fallback), 1))

    for column, (_, item) in zip(fallback_columns, fallback.iterrows()):
        render_product_card(
            column,
            item["product_id"],
            [f"近期购买 {int(item['buy_count'])} 次"]
        )

else:
    st.caption(
        f"最小距离 {min_distance:.2f}（≤ {DISTANCE_THRESHOLD}），"
        f"最接近的产品是 {nearest_product}，属于样例表覆盖范围。"
    )

with st.expander("查看异常客户记录表"):

    abnormal = load_abnormal()

    if abnormal.empty:
        st.caption("暂无记录。可切换到「输入新客户」并设置极端条件来触发。")
    else:
        st.dataframe(abnormal, use_container_width=True, hide_index=True)


# ==============================
# 11. 算法原理说明
# ==============================

with st.expander("查看推荐算法原理"):
    st.markdown(
        """
        本系统采用基于规则的风险匹配评分方法。

        客户风险评分：

        - 低风险：1
        - 中风险：3
        - 高风险：5

        产品风险评分：

        - 低风险产品：1
        - 中风险产品：3
        - 高风险产品：5

        匹配分数计算公式：

        `匹配分数 = 100 - abs(客户风险评分 - 产品风险评分) × 20`

        匹配分数越高，表示产品风险等级与客户偏好越接近。
        """
    )

    st.markdown(
        """
        多属性距离匹配（最近邻方法）：

        1. 每个字段建立一个归一化距离函数（输出域均为 0 到 1）：

           - 风险距离 = |客户评分 - 产品评分| / 4
           - 年龄距离：越靠近产品适龄区间中点越接近 0，区间内 0–0.5，区间外再累加到 1
           - 收入距离：越靠近产品目标收入区间中点越接近 0，区间内 0–0.5，区间外再累加到 1
             （收入低于起投金额时直接记为 1）

        2. 用加权欧氏距离组合：

           `d = sqrt(w风险×d风险² + w收入×d收入² + w年龄×d年龄²)`

        3. 综合匹配分 = 100 × (1 - d)

        原有公式不是另一种算法，而是三维加权距离在“单维 + 尺度 0.2”
        下的特例，因此两种排序依据共用同一段计算代码。
        """
    )

    st.markdown(
        """
        关联算法（Apriori 简化版）：

        1. 把购买记录按「同一客户同一天」聚合成订单；
        2. 先求频繁 1-项集，再求频繁 2-项集（只关注两个商品之间的关联）；
        3. 每个 2-项集生成两条规则，用三个指标筛选：

           - 支持度 = 同时购买该组合的订单数 / 订单总数
           - 置信度 = 买了前项之后再买后项的订单比例
           - 兴趣度 = 置信度 / 后项本身的支持度，大于 1 才说明前项对后项有提升作用

        4. 客户刚买的商品命中规则前项时，输出对应的后项作为「可能还想买」
        """
    )


# ==============================
# 12. 免责声明
# ==============================

st.divider()

st.caption(
    """
    免责声明：本系统仅用于课程实验和推荐算法演示。
    所有客户及金融产品数据均为模拟数据。
    推荐结果仅反映风险等级匹配程度，不构成实际投资建议，
    不代表真实金融产品的收益表现或适当性判断。
    """
)
