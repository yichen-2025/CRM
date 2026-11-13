
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

CUSTOMER_FILE = DATA_DIR / "customers.csv"
PRODUCT_FILE = DATA_DIR / "products.csv"


# ==============================
# 2. 初始化模拟数据
# ==============================

RISK_SCORE = {
    "低风险": 1,
    "中风险": 3,
    "高风险": 5
}


def create_sample_data():
    """当CSV文件不存在时，自动生成模拟数据。"""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CUSTOMER_FILE.exists():
        customers = pd.DataFrame([
            ["C001", "客户001", 25, 8, "低风险"],
            ["C002", "客户002", 28, 10, "低风险"],
            ["C003", "客户003", 35, 12, "低风险"],
            ["C004", "客户004", 30, 15, "中风险"],
            ["C005", "客户005", 32, 18, "中风险"],
            ["C006", "客户006", 38, 20, "中风险"],
            ["C007", "客户007", 42, 25, "中风险"],
            ["C008", "客户008", 26, 16, "中风险"],
            ["C009", "客户009", 40, 30, "高风险"],
            ["C010", "客户010", 45, 35, "高风险"],
            ["C011", "客户011", 29, 22, "高风险"],
            ["C012", "客户012", 50, 40, "高风险"],
            ["C013", "客户013", 33, 13, "低风险"],
            ["C014", "客户014", 37, 24, "中风险"],
            ["C015", "客户015", 48, 32, "高风险"],
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
            ["P001", "稳健理财A", "固定收益类理财", "低风险", 1],
            ["P002", "指数基金B", "指数型基金", "中风险", 3],
            ["P003", "黄金积存C", "贵金属投资", "中风险", 3],
            ["P004", "成长基金D", "权益类基金", "高风险", 5],
        ], columns=[
            "product_id",
            "product_name",
            "product_type",
            "risk_level",
            "risk_score"
        ])

        products.to_csv(
            PRODUCT_FILE,
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

    customer_columns = {
        "customer_id", "name", "age", "income", "risk_level"
    }

    product_columns = {
        "product_id", "product_name",
        "product_type", "risk_level", "risk_score"
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

    return customers, products


# ==============================
# 4. 产品推荐算法
# ==============================

def recommend_products(customer, products):
    """
    根据客户风险偏好计算产品匹配分数。

    匹配分数 = 100 - |客户风险评分 - 产品风险评分| * 20
    """

    customer_score = RISK_SCORE[customer["risk_level"]]

    result = products.copy()

    result["match_score"] = (
        100 - (
            customer_score - result["risk_score"]
        ).abs() * 20
    )

    result["match_score"] = result["match_score"].clip(0, 100)

    result["recommendation_reason"] = result.apply(
        lambda row: get_reason(
            customer["risk_level"],
            row["risk_level"],
            row["match_score"]
        ),
        axis=1
    )

    result = result.sort_values(
        by=["match_score", "product_name"],
        ascending=[False, True]
    ).reset_index(drop=True)

    result.insert(
        0,
        "ranking",
        range(1, len(result) + 1)
    )

    return result


def get_reason(customer_risk, product_risk, score):
    """生成简单的产品推荐理由。"""

    if customer_risk == product_risk:
        return "产品风险等级与客户风险偏好一致，匹配程度较高。"

    if score >= 60:
        return "产品风险等级与客户偏好较为接近。"

    return "产品风险等级与客户偏好存在一定差异。"


# ==============================
# 5. 页面标题
# ==============================

st.title("💰 SmartFinance CRM")
st.subheader("金融产品智能推荐系统")

st.markdown(
    """
    本系统通过分析客户的基本信息和风险偏好，
    利用风险匹配评分方法，为客户提供个性化金融产品推荐。
    """
)

st.divider()


# ==============================
# 6. 加载数据
# ==============================

try:
    create_sample_data()
    customers, products = load_data()

except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"数据加载失败：{error}")
    st.stop()


# ==============================
# 7. 客户选择与信息展示
# ==============================

st.header("一、客户信息管理")

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

col1, col2, col3, col4 = st.columns(4)

col1.metric("客户编号", customer["customer_id"])
col2.metric("客户年龄", f"{customer['age']} 岁")
col3.metric("年收入", f"{customer['income'] / 10000:.1f} 万元")
col4.metric("风险偏好", customer["risk_level"])

st.divider()


# ==============================
# 8. 金融产品展示
# ==============================

st.header("二、金融产品展示")

product_columns = st.columns(len(products))

for column, (_, product) in zip(product_columns, products.iterrows()):
    with column:
        st.markdown(f"### {product['product_name']}")
        st.write(product["product_type"])
        st.write(f"风险等级：{product['risk_level']}")
        st.write(f"风险评分：{product['risk_score']}")


st.divider()


# ==============================
# 9. 智能推荐
# ==============================

st.header("三、智能产品推荐")

recommendation = recommend_products(customer, products)

st.markdown(
    f"当前分析客户：**{customer['name']}**，"
    f"风险偏好：**{customer['risk_level']}**"
)

best_product = recommendation.iloc[0]

st.success(
    f"首选推荐产品：{best_product['product_name']} "
    f"（匹配分数：{best_product['match_score']:.0f}）"
)

st.subheader("产品推荐排名")

display_columns = [
    "ranking",
    "product_name",
    "product_type",
    "risk_level",
    "match_score",
    "recommendation_reason"
]

display_data = recommendation[display_columns].rename(
    columns={
        "ranking": "推荐排名",
        "product_name": "产品名称",
        "product_type": "产品类型",
        "risk_level": "风险等级",
        "match_score": "匹配分数",
        "recommendation_reason": "推荐理由"
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
    )[["match_score"]]

    st.bar_chart(chart_data)

with col2:
    st.subheader("推荐结果说明")

    st.write(f"客户姓名：{customer['name']}")
    st.write(f"客户风险偏好：{customer['risk_level']}")
    st.write(f"首选推荐：{best_product['product_name']}")
    st.write(f"匹配分数：{best_product['match_score']:.0f}")

    st.info(
        best_product["recommendation_reason"]
    )


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
