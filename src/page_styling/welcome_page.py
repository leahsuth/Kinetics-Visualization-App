import pandas as pd
import io
from pathlib import Path
import streamlit as st

def larger_banner(title, subtitle=None):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #007A73 0%, #005a55 100%);
        color: white;
        padding: 1rem;
        margin: 0 -1rem 1rem -1rem;
        text-align: center;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,122,115,0.2);
    ">
        <h1 style="margin: 0; font-size: 3.0rem; font-weight: 700; letter-spacing: -0.02em;">{title}</h1>
        {f'<p style="margin: 0.5rem 0 0; font-size: 2.0rem; opacity: 0.9;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def about_banner(title, subtitle=None, full_width=False):
    width = "100%" if full_width else "85%"
    margin = "0 0 1rem 0" if full_width else "0 auto 1rem"
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #007A73 0%, #005a55 100%);
        color: white;
        padding: 0.5rem 0.9rem;
        margin: {margin};
        width: {width};
        text-align: center;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,122,115,0.2);
    ">
        <h1 style="margin: 0; font-size: 1.25rem; font-weight: 700;">{title}</h1>
    </div>
    """, unsafe_allow_html=True)

def about_main_body(title, subtitle=None):
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
