# pages/profit_calc.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

from tools.fifo import split_orders, calculate_fifo_cost
from tools.first_leg import calculate_first_leg_fee
from tools.last_leg import calculate_last_leg_fee
from tools.calculate_handling_fee import calculate_handling_fee

st.set_page_config(page_title="FREY - 利润核算", layout="wide")
st.title("📊 FREY 工具库 - 利润核算")

# -------------------- 会话状态 --------------------
for key, default in [('selected_year', None), ('selected_month', None),
                     ('data_loaded', False), ('engine', None),
                     ('sales_df', pd.DataFrame()), ('purchase_df', pd.DataFrame()),
                     ('warehouse_df', pd.DataFrame()), ('product_df', pd.DataFrame()),
                     ('shipping_rule_df', pd.DataFrame()), ('handling_rule_df', pd.DataFrame())]:
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------- 数据库连接 --------------------
with st.sidebar:
    st.header("数据库连接")
    host = st.text_input("主机", "localhost")
    port = st.text_input("端口", "3306")
    user = st.text_input("用户名", "root")
    password = st.text_input("密码", type="password", value="123456")
    db_name = st.text_input("数据库名称", "进销存数据库")
    connect_button = st.button("连接数据库并加载数据")

@st.cache_data(ttl=3600)
def load_data(_engine):
    sales_df = pd.read_sql("SELECT * FROM `销售明细表`", _engine)
    purchase_df = pd.read_sql("SELECT * FROM `采购入库单`", _engine)
    warehouse_df = pd.read_sql("SELECT * FROM `warehouse`", _engine)
    product_df = pd.read_sql("SELECT * FROM `货品主档`", _engine)
    shipping_rule_df = pd.read_sql("SELECT * FROM `运费收费规则`", _engine)
    handling_rule_df = pd.read_sql("SELECT * FROM `操作费收费规则`", _engine)
    return sales_df, purchase_df, warehouse_df, product_df, shipping_rule_df, handling_rule_df

# -------------------- 主流程 --------------------
if connect_button:
    try:
        engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4")
        st.session_state.engine = engine
        st.session_state.sales_df, st.session_state.purchase_df, st.session_state.warehouse_df, \
        st.session_state.product_df, st.session_state.shipping_rule_df, st.session_state.handling_rule_df = load_data(engine)
        st.session_state.data_loaded = True
        st.success("数据库连接成功，数据已加载！")
    except Exception as e:
        st.error(f"数据库连接失败或数据加载失败：{e}")

# -------------------- 数据展示 & 利润计算 --------------------
if st.session_state.data_loaded:
    sales_df = st.session_state.sales_df
    sales_df['日期'] = pd.to_datetime(sales_df['日期'], errors='coerce')

    year_list = sorted(sales_df['日期'].dt.year.dropna().unique().tolist())
    month_list = list(range(1, 13))
    if not st.session_state.selected_year:
        st.session_state.selected_year = year_list[0] if year_list else pd.Timestamp.now().year
    if not st.session_state.selected_month:
        st.session_state.selected_month = month_list[0]

    with st.sidebar:
        st.header("选择年月")
        st.session_state.selected_year = st.selectbox("年份", year_list, index=year_list.index(st.session_state.selected_year))
        st.session_state.selected_month = st.selectbox("月份", month_list, index=month_list.index(st.session_state.selected_month))

    filtered_preview = sales_df[
        (sales_df['日期'].dt.year == st.session_state.selected_year) &
        (sales_df['日期'].dt.month == st.session_state.selected_month)
    ]

    st.write(f"📄 {st.session_state.selected_year}年{st.session_state.selected_month}月销售数据预览，共 {len(filtered_preview)} 条记录")
    st.dataframe(filtered_preview, use_container_width=True)

    if st.sidebar.button("计算选定月份利润"):
        if filtered_preview.empty:
            st.warning("所选月份无销售数据")
        else:
            sales = filtered_preview.copy()
            sales = split_orders(sales)
            sales = calculate_fifo_cost(sales, st.session_state.purchase_df)
            sales = calculate_first_leg_fee(sales, st.session_state.warehouse_df, st.session_state.product_df)
            sales = calculate_last_leg_fee(sales, st.session_state.warehouse_df, st.session_state.product_df, st.session_state.shipping_rule_df)
            sales = calculate_handling_fee(sales, st.session_state.warehouse_df, st.session_state.product_df, st.session_state.handling_rule_df)

            # 利润计算
            for col in ['不含税总价','采购成本','头程费用','尾程配送费','操作费']:
                sales[col] = pd.to_numeric(sales[col], errors='coerce').fillna(0)
            sales['利润'] = sales['拆单不含税总价'] - sales['采购成本'] - sales['头程费用'] - sales['尾程配送费'] - sales['操作费']

            st.write(f"💰 {st.session_state.selected_year}年{st.session_state.selected_month}月利润计算结果")
            st.dataframe(sales, use_container_width=True)
