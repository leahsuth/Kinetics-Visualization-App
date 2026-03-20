import streamlit as st
from pathlib import Path
import io
import pandas as pd

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

def larger_banner(title, subtitle=None):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #007A73 0%, #005a55 100%);
        color: white;
        padding: 1rem;
        margin: 0 -1rem 1rem -1rem;
        text-align: center;
        border-radius: 0 0 12px 12px;
        box-shadow: 0 4px 12px rgba(0,122,115,0.2);
    ">
        <h1 style="margin: 0; font-size: 3.0rem; font-weight: 700; letter-spacing: -0.02em;">{title}</h1>
        {f'<p style="margin: 0.5rem 0 0; font-size: 2.0rem; opacity: 0.9;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def about_banner(title, subtitle=None):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #007A73 0%, #005a55 100%);
        color: white;
        padding: 0.5rem 0.9rem;
        margin: 0 auto 1rem;
        width: 85%;
        text-align: center;
        border-radius: 0 0 12px 12px;
        box-shadow: 0 4px 6px rgba(0,122,115,0.2);
    ">
        <h1 style="margin: 0; font-size: 1.25rem; font-weight: 700;">{title}</h1>
    </div>
    """, unsafe_allow_html=True)

def smaller_banner(title, subtitle=None):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #007A73 0%, #005a55 100%);
        color: white;
        padding: 0.35rem 0.75rem;
        margin: 0 auto 1rem;
        width: 85%;
        text-align: center;
        border-radius: 0 0 6px 6px;
        box-shadow: 0 4px 6px rgba(0,122,115,0.2);
    ">
        <h1 style="margin: 0; font-size: 1.25rem; font-weight: 700;">{title}</h1>
        {f'<p style="margin: 0.5rem 0 0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def blurb(title, subtitle=None):
    st.markdown(f"""
    <div style="
        background: white;
        color: black;
        padding: 0.5rem 0.9rem;
        margin: 0 auto 1rem;
        width: 85%;
        text-align: left;
        border-radius: 0 0 6px 6px;
        box-shadow: 0 4px 6px rgba(0,122,115,0.2);
    ">
        <div style="margin: 0; font-size: 1.1rem;">{title}</div>
    </div>
    """, unsafe_allow_html=True)

larger_banner("Welcome to the Kinetics Visualization App!", "Upload data, visualize plates, and analyze peak areas")

st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)

about_banner("About")

blurb("""This app is designed to streamline and automate the process of visualizing and analyzing kinetic data from HPLC experiments. Currently, it supports the following features:<br><br>
       <ul style="text-align: left; display: inline-block; margin: 0.5rem 0 0;">
         <li>Generating plate layouts from reaction conditions</li>
         <li>Graphing Peak Area over Time</li>
         <li>Graphing Peak Area Percent over Time</li>
         <li>Calculating initial rates</li>
         <li>Downloading plots as PNGs</li>
         <li>Unit conversion</li>
       </ul>""")

st.markdown("<div style='height: 6rem;'></div>", unsafe_allow_html=True)
smaller_banner("Instructions")

#Slideshow
SLIDES_DIR = Path(__file__).parent / "assets"
image_files = ["Initial_input.png", "Kinetics.png", "Unit_Conversions.png"]
paths = [SLIDES_DIR / f for f in image_files if (SLIDES_DIR / f).exists()]

if paths:
  if "slide_idx" not in st.session_state:
      st.session_state["slide_idx"] = 0
  n = len(paths)
  idx = st.session_state["slide_idx"]


  # Put arrows on left and right of the slideshow
  col_prev, col_img, col_next = st.columns([0.5, 6, 0.5])
  with col_prev:
    st.markdown("<div style='height: 12rem;'></div>", unsafe_allow_html=True)
    if st.button("◀", use_container_width=True, key="prev"):
      st.session_state["slide_idx"] = (idx - 1) % n
      st.rerun()
  with col_img:
    st.image(str(paths[idx]), use_container_width=True)
    st.caption(f"{idx + 1} / {n}")
  with col_next:
    st.markdown("<div style='height: 12rem;'></div>", unsafe_allow_html=True)
    if st.button("▶", use_container_width=True, key="next"):
      st.session_state["slide_idx"] = (idx + 1) % n
      st.rerun()

smaller_banner("Let's Get Started!")

#download template
def excel_template_bytes() -> bytes:
    df = pd.DataFrame(
        [
            {"Reaction": "1", "Reaction_Well": "A1", "Timepoint": "0",  "Condition1": "LigA", "Condition2": "Cat1"},
            {"Reaction": "2", "Reaction_Well": "A2", "Timepoint": "5",  "Condition1": "",     "Condition2": "Cat2"},
            {"Reaction": "",  "Reaction_Well": "",   "Timepoint": "10", "Condition1": "",     "Condition2": ""},
        ]
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Experiment")
    return buf.getvalue()


_, col_dl, col_guide, _ = st.columns([1, 1, 1, 1])
with col_dl:
    downloaded = st.download_button(
        label="Download template",
        data=excel_template_bytes(),
        file_name="experiment_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    if downloaded:
        st.switch_page("pages/Initial_Input.py")
with col_guide:
    with st.popover("Template guide", use_container_width=True):
        st.markdown(
            "| Column | Required? | Notes |\n"
            "|---|---|---|\n"
            "| **Reaction** | Yes | Unique reaction ID |\n"
            "| **Timepoint** | Yes | One row per timepoint |\n"
            "| **Reaction_Well** | Yes | e.g. A1, B3 |\n"
            "| Any custom name | Optional | Add as many condition columns as needed (e.g. Ligand, Catalyst, Solvent) |"
        )