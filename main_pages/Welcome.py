import streamlit as st
from pathlib import Path
import io
import pandas as pd
from src.page_styling.welcome_page import (
    larger_banner, 
    about_banner, 
    about_main_body, 
    help_dialog)

st.set_page_config(
    page_title="Kinetics Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open("index.css", "r") as file:
    css = file.read()

st.html(f"<style>{css}</style>")


st.logo(image='assets/Merck_Logo.png')

larger_banner("Welcome to the Kinetics Visualization App!", "Upload data, visualize reaction plots, and calculate initial rates.")


# Let's Get Started banner + help in corner
SLIDES_DIR = Path(__file__).parent.parent / "assets"
instruction_images = ["Initial_input.png", "Kinetics_main_plot.png", "Kinetics_initial_rate.png", "Utilities.png"]
instruction_paths = [SLIDES_DIR / f for f in instruction_images if (SLIDES_DIR / f).exists()]

about_main_body()

col_cta, col_help = st.columns(2)
with col_cta:
    if st.button(
        "Let's get started!",
        type="primary",
        width="stretch",
        key="cta_Initial_Input",
    ):
        st.switch_page("main_pages/Initial_Input.py")
with col_help:
    help_button = st.button("Click for Instructions!", width="stretch")
    if help_button:
        help_dialog(instruction_paths)

