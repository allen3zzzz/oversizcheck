import streamlit as st
from tools import oversize_check
from tools import example_tool

st.set_page_config(page_title="FREY 工具库", layout="wide")
st.sidebar.title("FREY 工具库功能")

menu = ["超大件判定", "示例工具"]
choice = st.sidebar.radio("选择功能", menu)

if choice == "超大件判定":
    oversize_check.run_oversize_check()
elif choice == "示例工具":
    example_tool.run_example_tool()
