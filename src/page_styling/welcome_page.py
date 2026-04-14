import pandas as pd
import io
from pathlib import Path
import streamlit as st


def larger_banner(title, subtitle=None):
    st.html(
    f"""
    <div class="larger-banner">
        <h1>{title}</h1>
        {f'<p>{subtitle}</p>' if subtitle else ""}
    </div>
    """
    )

def about_banner(title):
    st.html(
    f"""
    <div class="about-banner">
        <h1>{title}</h1>
    </div>
    """
    )

def about_main_body():
    st.html(
    """
    <div class="about-main-body">
        <div class="about-content">
            This app is designed to streamline and automate the process 
            of visualizing and analyzing kinetic data from HPLC experiments. 
            Currently, it supports the following features:<br><br>
            <ul>
                <li>Generating plate layouts from reaction conditions</li>
                <li>Graphing Peak Area over Time</li>
                <li>Graphing Peak Area Percent over Time</li>
                <li>Calculating initial rates </li>
                <li>Graphing exponential fit of reactions</li>
                <li>Downloading plots as PNGs</li>
                <li>Solving common laboratory calculations</li>
            </ul>
       </div>
    </div>
   """
    )

def excel_template_bytes() -> bytes:
    df = pd.DataFrame(
        [
            {
                "Reaction": "1",
                "Reaction_Well": "A1",
                "Timepoint": "0",
                "Condition1": "LigA",
                "Condition2": "Cat1",
            },
            {
                "Reaction": "2",
                "Reaction_Well": "A2",
                "Timepoint": "5",
                "Condition1": "",
                "Condition2": "Cat2",
            },
            {
                "Reaction": "",
                "Reaction_Well": "",
                "Timepoint": "10",
                "Condition1": "",
                "Condition2": "",
            },
        ]
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Experiment")
    return buf.getvalue()
