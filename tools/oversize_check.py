import streamlit as st
import pandas as pd

# ---------- 核心逻辑 ----------
def classify_oversize(df):
    cm_to_in = 0.393701
    kg_to_lb = 2.20462

    # 判断使用外箱或内箱
    length_col = "外箱-长(CM)" if "外箱-长(CM)" in df.columns else "内箱-长(CM)"
    width_col = "外箱-宽(CM)" if "外箱-宽(CM)" in df.columns else "内箱-宽(CM)"
    height_col = "外箱-高(CM)" if "外箱-高(CM)" in df.columns else "内箱-高(CM)"
    weight_col = "外箱-净重(KG)" if "外箱-净重(KG)" in df.columns else "内箱-毛重(KG)"
    circum_col = "外箱-围长（CM）" if "外箱-围长（CM）" in df.columns else "内箱-围长（CM）"

    df['长(in)'] = df[length_col] * cm_to_in
    df['宽(in)'] = df[width_col] * cm_to_in
    df['高(in)'] = df[height_col] * cm_to_in
    df['围长(in)'] = df[circum_col].fillna(df['长(in)'] + 2*(df['宽(in)']+df['高(in)']))
    df['重量(lb)'] = df[weight_col] * kg_to_lb
    df['体积重(lb)'] = df['长(in)']*df['宽(in)']*df['高(in)']/139

    # 超大件判定
    def judge_oversize(row):
        if (row['长(in)']>59 or row['宽(in)']>33 or row['高(in)']>33
            or row['围长(in)']>130 or max(row['重量(lb)'], row['体积重(lb)'])>50):
            return "超大件"
        return "非超大件"

    df['超大件判定'] = df.apply(judge_oversize, axis=1)

    # 原尺寸分类
    def classify_size(row):
        if row['超大件判定']=="超大件":
            return "超大件"
        elif row['重量(lb)'] <= 1 and row['长(in)']<=15 and row['宽(in)']<=12 and row['高(in)']<=0.75:
            return "小号标准尺寸"
        elif row['重量(lb)'] <= 20 and row['长(in)']<=18 and row['宽(in)']<=14 and row['高(in)']<=8:
            return "大号标准尺寸"
        elif row['重量(lb)'] <= 50 and row['长(in)']<=59 and row['宽(in)']<=33 and row['高(in)']<=33 and row['围长(in)']<=130:
            return "大号大件"
        else:
            return "超大件"

    df['尺寸分类'] = df.apply(classify_size, axis=1)
    df['一致性'] = df.apply(lambda row: "一致" if row['尺寸分类']==row['超大件判定'] else "不一致", axis=1)
    df['最终分类'] = df['尺寸分类']

    return df

# ---------- Streamlit 页面 ----------
def run_oversize_check():
    st.title("📦 超大件判定工具")
    uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx", "xls"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        result_df = classify_oversize(df)
        st.dataframe(result_df)

        # 下载结果
        output = "result.xlsx"
        result_df.to_excel(output, index=False, engine="xlsxwriter")
        with open(output, "rb") as f:
            st.download_button("下载结果", data=f, file_name="result.xlsx")
