from src.form import foo_bar
import streamlit as st

st.set_page_config(
    page_title="Merck Kinetics Application", 
    page_icon="👋",
    layout='wide')

st.write("# MSSE KInetics Project")

with st.form("my_from"):
    st.write("Inside the form")
    my_number = st.slider("Pick a number", 1, 10)
    my_color = st.selectbox(
        "Pick a color", ["red", "orange", "green", "blue", "violet"]
    )
    st.form_submit_button('Submit my picks')

st.write(my_number)
st.write(my_color)
