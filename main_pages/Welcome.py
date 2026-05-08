import streamlit as st
from pathlib import Path
import io
import pandas as pd
from src.page_styling.welcome_page.banners import (
    larger_banner, 
    about_banner, 
    about_main_body, 
    )
from src.page_styling.welcome_page.instructions import help_dialog

st.set_page_config(
    page_title="Kinetics Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo(image='assets/Merck_Logo.png')

larger_banner("Welcome to the Kinetics Visualization App!", "Upload data, visualize reaction plots, and calculate initial rates.")

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
        help_dialog()

st.markdown(
    """
    <style>
      /* Keep page content above fixed footer */
      .stMainBlockContainer {
        padding-bottom: 3.25rem;
      }
      .app-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        color: #6b7280;
        font-size: 0.9rem;
        background: rgba(255, 255, 255, 0.92);
        border-top: 1px solid #e5e7eb;
        padding: 0.5rem 0.75rem;
        z-index: 999;
        backdrop-filter: blur(2px);
      }
    </style>
    <div class="app-footer">
      Built by: Trisha Kholiya, Randa Lateef, James McTighe, Leah Sutherland
    </div>
    """,
    unsafe_allow_html=True,
)

