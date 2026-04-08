import streamlit as st
from pathlib import Path
import io
import pandas as pd
from src.page_styling.welcome_page import larger_banner, about_banner, about_main_body, excel_template_bytes

st.set_page_config(
    page_title="Kinetics Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    .block-container { max-width: 98%; }
    </style>
    """, unsafe_allow_html=True)

st.logo(image='assets/Merck_Logo.png')

larger_banner("Welcome to the Kinetics Visualization App!", "Upload data, visualize reaction plots, and calculate initial rates.")

st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)

# Let's Get Started banner + help in corner
SLIDES_DIR = Path(__file__).parent / "assets"
instruction_images = ["Initial_input.png", "Kinetics.png", "Unit_Conversions.png"]
instruction_paths = [SLIDES_DIR / f for f in instruction_images if (SLIDES_DIR / f).exists()]

col_left, col_banner, col_help = st.columns([1.5, 17, 1.5])
with col_left:
    st.empty()
with col_banner:
    about_banner("Let's Get Started!", full_width=True)
with col_help:
    st.markdown("<div style='height: 0.25rem;'></div>", unsafe_allow_html=True)
    with st.popover("?", help="Click for instructions"):
        st.caption("**Instructions**")
        if instruction_paths:
            if "slide_idx" not in st.session_state:
                st.session_state["slide_idx"] = 0
            n = len(instruction_paths)
            idx = st.session_state["slide_idx"]
            # Put arrows on left and right of the slideshow
            col_prev, col_img, col_next = st.columns([0.5, 6, 0.5])
            with col_prev:
                st.markdown("<div style='height: 12rem;'></div>", unsafe_allow_html=True)
                if st.button("◀", use_container_width=True, key="prev"):
                    st.session_state["slide_idx"] = (idx - 1) % n
                    st.rerun()
            with col_img:
                st.image(str(instruction_paths[idx]), use_container_width=True)
                st.caption(f"{idx + 1} / {n}")
            with col_next:
                st.markdown("<div style='height: 12rem;'></div>", unsafe_allow_html=True)
                if st.button("▶", use_container_width=True, key="next"):
                    st.session_state["slide_idx"] = (idx + 1) % n
                    st.rerun()
            st.caption(f"{idx + 1} / {n}")

st.markdown("""
<style>
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #2E7D32 !important;
    border-color: #2E7D32 !important;
    color: white !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #1B5E20 !important;
    border-color: #1B5E20 !important;
}
</style>
""", unsafe_allow_html=True)

_, col_cta, _ = st.columns([1, 2, 1])
with col_cta:
    if st.button(
        "Click here to begin",
        type="primary",
        use_container_width=True,
        key="cta_Initial_Input",
    ):
        st.switch_page("pages/Initial_Input.py")

about_banner("About")

about_main_body("""This app is designed to streamline and automate the process of visualizing and analyzing kinetic data from HPLC experiments. Currently, it supports the following features:<br><br>
       <ul style="text-align: left; display: inline-block; margin: 0.5rem 0 0;">
         <li>Generating plate layouts from reaction conditions</li>
         <li>Graphing Peak Area over Time</li>
         <li>Graphing Peak Area Percent over Time</li>
         <li>Calculating initial rates</li>
         <li>Downloading plots as PNGs</li>
         <li>Unit conversion</li>
       </ul>""")
