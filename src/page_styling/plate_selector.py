import streamlit as st
import string

def list_of_letters(n):
    pass

def clear_all_wells():
    st.session_state.selected_wells = set()

def button_type(is_selected):
    if is_selected:
        return 'primary'
    else:
        return 'secondary'

def render_well_plate(num_rows=5, num_cols=5):
    """Renders the plate and returns the list of selected wells."""
    st.subheader("Plate Layout")
    
    rows = list(string.ascii_uppercase[:num_rows])
    cols = [str(i) for i in range(1, num_cols + 1)]
    col_weights = [0.5] + [1] * 12

    if 'selected_wells' not in st.session_state:
        st.session_state.selected_wells = set()


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
            
            if cols_list[i+1].button(well_id, key=well_id, type=button_type(is_selected)):
                if well_id in st.session_state.selected_wells:
                    st.session_state.selected_wells.remove(well_id)
                else:
                    st.session_state.selected_wells.add(well_id)
                st.rerun()

    st.button("Clear all wells", on_click=clear_all_wells, type='primary')
    
    # Return the sorted list so other parts of the app can use it
    return sorted(list(st.session_state.selected_wells))
