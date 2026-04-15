import streamlit as st

welcome = st.Page("Welcome.py", title="Welcome", default=True)
input = st.Page("pages/Initial_Input.py", title="Initial Input")
kinetics = st.Page("pages/Kinetics.py", title="Kinetics")
utilities = st.Page("pages/Utilities.py", title="Utilities")

pg = st.navigation(
    [welcome, input, kinetics, utilities],
    position="top"
)

pg.run()
