import streamlit as st

def instruction_banner_skeleton(title, sub_header, content):
    st.html(
       f"""
        <div class="instructions-box">
            <h1>{title}</h1>
            <h2>{sub_header}</h2>
            <div class="instructions-content">{content}</div>
        </div>
        """
    )

def data_upload_instruction():
    content_text = """
        <ol>
            <li>Determine if the HPLC datafile is Chemstation data or processed data.</li>
            <li>Upload the Experiment Conditions (Download and fill out template as needed.</li>
            <li>Upload the HPLC datafile.</li>
            <li>If desired, visualize plates and color wells by Reaction Conditions.</li>
            <li>Save setup before proceeding to the rate Information and plotting page.</li>
        </ol>
        """
    instruction_banner_skeleton(
        title="🧪 Data Upload", 
        sub_header="Configure reactions and visualize reactions plates",
        content=content_text
    )

def kinetics_instruction():
    content_text = """
        <ol>
            <li>Enter a value for rate constant (k)</li>
            <li>(optional) Manually select growth/decay profile per analyte</li>
            <li>View rate summary tables for chosen reactions & analytes.</li>
            <li>Select which analytes to fit for each reaction.</li>
            <li>Add/Delete plots for export report</li>
            <li>Export report and download processed data file.</li>
        </ol>
        """
    instruction_banner_skeleton(
        title="📈 rate information and plotting: initial rate", 
        sub_header="Generate rate summary tables & exponential fit plots",
        content=content_text
    )

def inital_rate_instruction():
    content_text = """
        <h1>Kinetics Plot:</h1>
        <ol>
            <li>Select reactions to plot</li>
            <li>Select time units (days, hours, minutes, seconds)</li>
            <li>Select analytes to plot</li>
            <li>Color plot by reacant or reaction</li>
            <li>Choose plot type (scatter or line).  Determine if plots should be generated for each reaction.  Reactions can optionally be set to display as seperate plots.</li>
        </ol>
        <h1>Analyte Ratio Plot:</h1>
        <ol>
            <li>Choose plot type (scatter or line)</li>
            <li>Choose a numerator & denominator</li>
        </ol>
        """
    instruction_banner_skeleton(
        title="📈 Rate information and plotting: Kinetics and analyte ratio", 
        sub_header="Visualize Peak Area vs. Time & Analyte Ratio vs. Time",
        content=content_text
    )

def utilities_instruction():
    content_text = """
        <h1>Solves For:</h1>
        <ol>
            <li>
                Concentration Calculations
                <ul>
                    <li>Mass from Volume and Concentration</li>
                    <li>Volume from Mass and Concentration</li>
                    <li>Concentration from Mass & Volume</li>
                </ul>
            </li>
            <li>Dilutions</li>
            <li>Enantiomeric / Diasterometric Excess</li>
        </ol>
        """
    instruction_banner_skeleton(
        title="⚙️ Utilities", 
        sub_header="Common mathematical calculations performed in a laboratory setting.",
        content=content_text
    )

@st.dialog("Application Instructions", width="medium")
def help_dialog():
    tab1, tab2, tab3, tab4 = st.tabs([
        "Data Upload",
        "Kinetics and Analyte Ratio",
        "Initial Rate",
        "Utilities"
    ])

    with tab1:
        data_upload_instruction()
    with tab2:
        kinetics_instruction()
    with tab3:
        inital_rate_instruction()
    with tab4:
        utilities_instruction()
