import streamlit as st


def setup_header():
    st.html(
        """
        <div class="setup-header">
            <h1>Experiment Setup</h1>
            <p >Upload your conditions and HPLC files, configure reactions, then save to proceed.</p>
        </div>
        """
    )

def step_label(number, label):
    st.html(
        f"""
        <div class='step-row'>
        <span class='step-badge'>{number}</span>
        <span class='step-title'>{label}</span>
        </div>
        """
    )

def data_source_help_text():
    with st.expander("Which data source type should I choose?", expanded=False):
        st.html(
            """
            <div class="data-source-help-text">
                <div>
                    <h2>ChemStation</h2>Use this when you are working from <b>Agilent ChemStation exports</b>
                    and want the app to tie experiments to a <b>conditions</b> spreadsheet.
                    <ul>
                        <li>You upload <b>two</b> files: experiment conditions (<code>.xlsx</code>) and HPLC results (<code>.xlsx</code>).</li>
                        <li>You map reactions, wells, and timepoints, and can use the <b>plate editor</b>.</li>
                    </ul>
                </div>
                <div>
                    <h2>Processed</h2>Use this when you already have a <b>single table</b> of kinetics that is
                    <b>ready to plot</b> (time column + one column per analyte).
                    <ul>
                        <li>You upload <b>one</b> file (<code>.csv</code> or <code>.xlsx</code>); no separate conditions file.</li>
                        <li>Reactions are inferred from the file (e.g. when time resets between runs).</li>
                        <li>Open How processed files should look below for an example table layout.</li>
                    </ul>
                </div>
            </div>
            """
        )

def preprocessed_file_example():
    with st.expander("How processed files should look (example table)", expanded=False):
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
