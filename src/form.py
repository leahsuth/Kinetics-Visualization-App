import streamlit as st

def foo_bar():
    with st.form("hello"):
        st.write("### Yo this is my form mr white")
        st.form_submit_button('Science bitch!')
