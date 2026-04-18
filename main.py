import streamlit as st

if "experiment_setup" not in st.session_state:
    st.session_state.experiment_setup = None

welcome = st.Page("main_pages/Welcome.py", title="Welcome", default=True)
input = st.Page("main_pages/Initial_Input.py", title="Data Upload")
kinetics = st.Page("main_pages/Kinetics.py", title="Rate Information and Plotting")
utilities = st.Page("main_pages/Utilities.py", title="Utilities")

pages = [welcome,input, kinetics, utilities] 

pg = st.navigation(
    pages
)

pg.run()
