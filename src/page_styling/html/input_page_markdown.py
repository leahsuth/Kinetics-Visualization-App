import streamlit as st


def input_page_setup():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 0; padding-bottom: 2rem; max-width: 1200px; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }
        .section-label {
            font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em;
            text-transform: uppercase; color: rgba(49,51,63,.45); margin-bottom: 4px;
        }
        .step-row {
            display: flex; align-items: center; gap: 10px; margin: 1.2rem 0 0.4rem 0;
        }
        .step-badge {
            display: inline-flex; align-items: center; justify-content: center;
            width: 28px; height: 28px; border-radius: 50%;
            background: #007A73; color: white;
            font-size: 0.82rem; font-weight: 700; flex-shrink: 0;
        }
        .step-title {
            font-size: 1.05rem; font-weight: 700; color: #1f2937; margin: 0;
        }
        .upload-card-label {
            font-size: 1rem; font-weight: 700; margin-bottom: 2px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def setup_header():
    st.markdown("""
        <style>
        .block-container { max-width: 80%; }
        </style>
        """, unsafe_allow_html=True)
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #007A73 0%, #005a55 100%);
            color: white;
            padding: 1rem;
            margin: 2rem;
            text-align: center;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,122,115,0.2);
        ">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; letter-spacing: -0.02em;">Experiment Setup</h1>
            <p style="margin: 0.4rem; font-size: 1rem; opacity: 0.88;">Upload conditions plus either ChemStation HPLC data or processed measurements, configure reactions, then save to proceed.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def step_label(number, label):
    st.markdown(
        "<div class='step-row'>"
        f"<span class='step-badge'>{number}</span>"
        f"<span class='step-title'>{label}</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def data_source_help_text():
    with st.expander("Which data source type should I choose?", expanded=False):
        st.markdown(
            """
**ChemStation** — Use this when you are working from **Agilent ChemStation exports**
and want the app to tie experiments to a **conditions** spreadsheet.

- You upload **two** files: experiment conditions and HPLC results.
- In the conditions file: map reactions, wells, and timepoints. 
- For the HPLC File: Upload directly from ChemStation

**Processed** — Use this when you already have **processed kinetics data** ready to plot. This data
should include a **Reaction** column and **time** column, with one column per analyte.

- You upload **two** files: experiment conditions and **processed measurements**.
- Conditions define **reaction IDs**, **# of Timepoints** (per reaction),
  optional **Reaction_Well** for plate analysis, and any extra condition columns.
- Processed data must include a **Reaction** column, plus one column per analyte.
  There should only be one measurement type per file (e.g. all concentration).
- Open **How processed files should look** below for the measurements layout.
"""
        )


def preprocessed_file_example():
    with st.expander("How processed files should look (example table)", expanded=False):
        st.markdown(
            """
**Measurements file** — use a **wide** table: one row per reaction per timepoint, **one column for time**, and **one column per analyte**
(with numeric measurements). Use **one measurement type** per file (e.g. all concentrations or all areas).

| Column | Required? | Notes |
|--------|-----------|-------|
| **Reaction** | Yes | Must match the **Reaction** IDs present in the conditions spreadsheet. |
| **Time** | Yes | Time values corresponding to the reaction measurements. |
| All other numeric columns | At least one | **Analytes** (e.g. product, impurity). |

**Example** (CSV / Excel):

| Reaction | time | ANALYTE1 | ANALYTE2 |
|----------|------|-----------|-----------|
| 1 | 0 | 0.10 | 0.90 |
| 1 | 5 | 0.35 | 0.63 |
| 2 | 0 | 0.12 | 0.88 |
| 2 | 5 | 0.40 | 0.58 |


**Validation note:** For Processed mode, the app checks row counts per reaction against **# of Timepoints** in the conditions file.
            """
        )
