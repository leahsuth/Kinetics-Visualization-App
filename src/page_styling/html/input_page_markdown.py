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
            <p style="margin: 0.4rem; font-size: 1rem; opacity: 0.88;">Upload your conditions and HPLC files, configure reactions, then save to proceed.</p>
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

    - You upload **two** files: experiment conditions (`.xlsx`) and HPLC results (`.xlsx`).
    - You map reactions, wells, and timepoints, and can use the **plate editor**.

    **Preprocessed** — Use this when you already have a **single table** of kinetics that is
    **ready to plot** (time column + one column per analyte).

    - You upload **one** file (`.csv` or `.xlsx`); no separate conditions file.
    - Reactions are inferred from the file (e.g. when time resets between runs).
    - Open **How preprocessed files should look** below after selecting Preprocessed for an example layout.

            """
        )

def preprocessed_file_example():
    with st.expander("How preprocessed files should look (example table)", expanded=False):
        st.markdown(
            """
This table should only contain ONE measurement type.Use a **wide** table: one row per timepoint per sample, **one column for time**, and **one column per analyte**
(with numeric measurements). The **first column** can be any sample or run label; it is stored as **Sample Name**.

**Column names**

| Column | Required? | Notes |
|--------|-----------|-------|
| Sample Identifier | Recommended | Can be (identifier, well ID, etc.). |
| `time`, `Time`, or `timepoint` | Yes | Any unit is acceptable, but should be consistent throughout the file. |
| All other columns | At least one | Treated as **analytes** (e.g. product, impurity, internal standard). The value in this column should be the measurement of the analyte at that point of the run. |

**Reaction IDs** are assigned automatically: rows stay in the same reaction while time is non-decreasing; when **time drops** compared to the previous row, a **new reaction** starts (reaction 2, 3, …).

**Example** (CSV / Excel — same layout):

| Sample Identifier | time | ANALYTE_1 | ANALYTE_2 | ANALYTE_3 |
|-------------|------|---------|-----|----------|
| NB-001-01 | 0 | 0.10 | 0.90 | 0.00 |
| NB-001-01 | 2 | 0.35 | 0.63 | 0.02 |
| NB-001-01 | 4 | 0.58 | 0.40 | 0.02 |
| NB-002-01 | 0 | 0.12 | 0.88 | 0.00 |
| NB-002-01 | 2 | 0.40 | 0.58 | 0.02 |

Here the first three rows are **Reaction 1**. The next two rows start **Reaction 2**.
            """
        )
