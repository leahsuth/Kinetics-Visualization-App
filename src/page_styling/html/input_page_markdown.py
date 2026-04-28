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
                    <h2>Processed</h2> Use this when you already have processed kinetics data that is
                    <b>ready to plot</b> (time column + one column per analyte). <br>
                    <ul>
                        <li> This data should include a <b>Reaction</b> column and <b>time</b> column, with one column per analyte. <br>
                        <li> You upload <b>two</b> files: experiment conditions and processed measurements. <br>
                        <li> Conditions define <b>reaction IDs</b>, <b># of Timepoints</b> (per reaction), optional <b>Reaction_Well</b> for plate analysis, and any extra condition columns. <br>
                        <li> Processed data must include a <b>Reaction</b> column, plus one column per analyte. <br>
                        <li> There should only be one measurement type per file (e.g. all concentration). <br>
                        <li> Open <b>How processed files should look</b> below for the measurements layout.</li>
                    </ul>
                </div>
            </div>
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
