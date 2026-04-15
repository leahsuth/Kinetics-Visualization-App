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

with open("index.css", "r") as file:
    css = file.read()

st.html(f"<style>{css}</style>")


st.logo(image='assets/Merck_Logo.png')

larger_banner("Welcome to the Kinetics Visualization App!", "Upload data, visualize reaction plots, and calculate initial rates.")


# Let's Get Started banner + help in corner
SLIDES_DIR = Path(__file__).parent.parent / "assets"
instruction_images = ["Initial_input.png", "Kinetics_main_plot.png", "Kinetics_initial_rate.png", "Utilities.png"]
instruction_paths = [SLIDES_DIR / f for f in instruction_images if (SLIDES_DIR / f).exists()]

col_left, col_banner, col_help = st.columns([1.5, 17, 1.5])
with col_left:
    st.empty()
with col_banner:
    about_banner("Let's Get Started!")
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


_, col_cta, _ = st.columns([1, 2, 1])
with col_cta:
    if st.button(
        "📈  Visualize data and initial rates →",
        type="primary",
        use_container_width=True,
        key="cta_Initial_Input",
    ):
        st.switch_page("pages/Initial_Input.py")

about_banner("About")

about_main_body()
