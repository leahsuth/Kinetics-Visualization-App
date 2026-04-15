import streamlit as st

if "experiment_setup" not in st.session_state:
    st.session_state.experiment_setup = None

welcome = st.Page("main_pages/Welcome.py", title="Welcome", default=True)
input = st.Page("main_pages/Initial_Input.py", title="Data Upload")
kinetics = st.Page("main_pages/Kinetics.py", title="Rate Information and Plotting")
utilities = st.Page("main_pages/Utilities.py", title="Utilities")

pages = [welcome, input, utilities] 
if st.session_state.experiment_setup is not None:
    pages.append(kinetics)

pg = st.navigation(
    pages,
    position="top"
)

pg.run()
