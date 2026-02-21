import streamlit as st
import string
import colorsys

def list_of_letters(n):
    pass

def clear_all_wells():
    st.session_state.selected_wells = set()
    st.session_state.well_info = {}

def button_type(is_selected):
    if is_selected:
        return 'primary'
    else:
        return 'secondary'


def ph_to_color(ph):
    """Map pH (0–14) to rainbow gradient (red → orange → yellow → green → blue → violet)."""
    if ph is None:
        return None
    t = max(0, min(1, ph / 14))
    # Hue 0=red, 0.17=yellow, 0.33=green, 0.5=cyan, 0.67=blue, 0.83=violet
    hue = t * 0.83  # red at pH 0, violet at pH 14
    r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
    return f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"

def render_well_plate(num_rows=5, num_cols=5):
    """Renders the plate and returns the list of selected wells."""
    st.subheader("Plate Layout")
    
    rows = list(string.ascii_uppercase[:num_rows])
    cols = [str(i) for i in range(1, num_cols + 1)]
    col_weights = [0.5] + [1] * 12

    if 'selected_wells' not in st.session_state:
        st.session_state.selected_wells = set()
    if 'well_info' not in st.session_state:
        st.session_state.well_info = {}


    # pH color legend (rainbow)
    st.caption("Well colors: pH rainbow (red = low, violet = high)")
    st.markdown(
        '<div style="height:8px; background:linear-gradient(to right, '
        'rgb(255,0,0), rgb(255,127,0), rgb(255,255,0), rgb(0,255,0), rgb(0,255,255), rgb(0,0,255), rgb(128,0,255)); '
        'border-radius:4px; margin-bottom:8px;"></div>',
        unsafe_allow_html=True,
    )

    # Render Headers
    header_cols = st.columns(col_weights)
    for idx, col_num in enumerate(cols):
        header_cols[idx + 1].write(f"**{col_num}**")

    # Render Grid
    for row in rows:
        cols_list = st.columns(col_weights)
        cols_list[0].write(f"**{row}**")
        
        for i, col in enumerate(cols):
            well_id = f"{row}{col}"
            is_selected = well_id in st.session_state.selected_wells
            
            # Get pH for color gradient (red=low pH, blue=high pH)
            ph = None
            if well_id in st.session_state.well_info:
                info = st.session_state.well_info[well_id]
                ph = info.get("pH") if isinstance(info, dict) else None
            well_color = ph_to_color(ph) if ph is not None else None
            
            with cols_list[i + 1]:
                if well_color:
                    st.markdown(
                        f'<div style="height:4px; background:{well_color}; border-radius:2px; margin-bottom:2px;"></div>',
                        unsafe_allow_html=True,
                    )
                if st.button(well_id, key=well_id, type=button_type(is_selected)):
                    if well_id in st.session_state.selected_wells:
                        st.session_state.selected_wells.remove(well_id)
                    else:
                        st.session_state.selected_wells.add(well_id)
                    st.rerun()

    # Create text box where users can write info about selected wells
    if len(st.session_state.selected_wells) > 0:
        st.markdown("### Add information about the selected wells.")
        with st.form("bulk_edit"):
            ligand_name = st.text_input("Ligand Name *")
            timepoint = st.text_input("Timepoint *")
            catalyst_loading = st.number_input("Catalyst Loading *", min_value=0.0, max_value=100.0, step = 0.1)
            pH = st.number_input("pH *", min_value=0.00, max_value=14.00, step = 0.01)
            additional_notes = st.text_area("Additional Notes")
            submit_entry = st.form_submit_button("Apply entry to all selected wells.")

            if submit_entry:
                if ligand_name == "":
                    st.error("Ligand Name is required.")
                elif timepoint == "":
                    st.error("Timepoint is required.")
                elif catalyst_loading == 0:
                    st.error("Catalyst Loading is required.")
                elif pH == None:
                    st.error("pH is required.")
                else:
                    for well_id in st.session_state.selected_wells:
                        st.session_state.well_info[well_id] = {
                            "pH" : pH,
                            "timepoint" : timepoint,
                            "catalyst_loading" : catalyst_loading,
                            "additional_notes" : additional_notes
                        }
                st.session_state.selected_wells = set()
                st.rerun()

    # Show stored entries (persists across submits)
    st.write("Well Information:")
    if st.session_state.well_info:
        for well_id, info in sorted(st.session_state.well_info.items()):
            st.write(f"**{well_id}:** {info}")
    else:
        st.caption("No wells have information yet.")

    st.button("Clear all wells", on_click=clear_all_wells, type='primary', help="Clears selection and all stored well information.")
    
    # Return the sorted list so other parts of the app can use it
    return sorted(list(st.session_state.selected_wells))
