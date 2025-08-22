import streamlit as st


def run_example_tool():
    st.title("🛠 示例工具模块")
    st.write("这是一个示例子功能，你可以在这里实现其他功能。")

    name = st.text_input("输入你的名字")
    if st.button("提交"):
        st.success(f"Hello, {name}!")
