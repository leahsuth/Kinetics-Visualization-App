import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Kinetics Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo(image='assets/Merck_Logo.png')

# Teal banner
st.markdown("""
<div style="
    background: linear-gradient(135deg, #007A73 0%, #005a55 100%);
    color: white;
    padding: 1rem;
    margin: 0 -1rem 1rem -1rem;
    text-align: center;
    border-radius: 0 0 12px 12px;
    box-shadow: 0 4px 12px rgba(0,122,115,0.2);
">
    <h1 style="margin: 0; font-size: 3.0rem; font-weight: 700; letter-spacing: -0.02em;">
        Welcome to the Kinetics Visualization App!
    </h1>
    <p style="margin: 0.5rem 0 0; font-size: 2.0rem; opacity: 0.9;">
        Upload data, visualize plates, and analyze peak areas
    </p>
</div>
""", unsafe_allow_html=True)

# Instructions banner
st.markdown("""
<div style="
    background: linear-gradient(135deg, #007A73 0%, #005a55 100%);
    color: white;
    padding: 0.35rem 0.75rem;
    margin: 0 auto 1rem;
    width: 50%;
    text-align: center;
    border-radius: 0 0 6px 6px;
    box-shadow: 0 4px 6px rgba(0,122,115,0.2);
">
    <h1 style="margin: 0; font-size: 1.25rem; font-weight: 700; letter-spacing: -0.02em;">
        Instructions
    </h1>
</div>
""", unsafe_allow_html=True)

#to-do: Put in a blurb at the beginning explaining purpose of the app

# Slideshow button styling
st.markdown("""
<style>
  [data-testid="stButton"] button {
    padding: 0.2rem 0.6rem !important;
    font-size: 0.8rem !important;
  }
</style>
""", unsafe_allow_html=True)

#Slideshow
SLIDES_DIR = Path(__file__).parent / "assets"
image_files = ["Initial_Input.png", "Kinetics.png", "Unit_Conversions.png"]
paths = [SLIDES_DIR / f for f in image_files if (SLIDES_DIR / f).exists()]

if paths:
  if "slide_idx" not in st.session_state:
      st.session_state["slide_idx"] = 0
  n = len(paths)
  idx = st.session_state["slide_idx"]

  #center slideshow
  _, col_img, _ = st.columns([1, 2, 1])
  with col_img:
    st.image(str(paths[idx]), width=450)
    st.caption(f"{idx + 1} / {n}")

  #format buttons
  _, col_btns, _ = st.columns([1, 3, 1])
  with col_btns:
    btn_prev, btn_next = st.columns(2)
    with btn_prev:
      if st.button("◀ Prev", use_container_width=True, key="prev"):
        st.session_state["slide_idx"] = (idx - 1) % n
        st.rerun()
    with btn_next:
      if st.button("Next ▶", use_container_width=True, key="next"):
        st.session_state["slide_idx"] = (idx + 1) % n
        st.rerun()

#Format the "Let's get started" button
st.markdown("""
<style>
  [data-testid="stPageLink"] {
    display: inline-flex !important;
    align-items: center !important;
    padding: 0.5rem 1.25rem !important;
    border: 2px solid #007A73 !important;
    border-radius: 8px !important;
    text-decoration: none !important;
    transition: background 0.2s, color 0.2s !important;
  }
  [data-testid="stPageLink"]:hover {
    background: #007A73 !important;
    color: white !important;
  }
</style>
""", unsafe_allow_html=True)
_, col_link, _ = st.columns([1, 1, 1])
with col_link:
  st.page_link("pages/Initial_Input.py", label="Let's Get Started!", icon="🧪")


