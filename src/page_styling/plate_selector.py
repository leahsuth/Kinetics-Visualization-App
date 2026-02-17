import streamlit as st

def render_well_plate():
    """Renders the plate and returns the list of selected wells."""
    st.html('index.css')
    st.subheader("Plate Layout")
    
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    cols = [str(i).zfill(2) for i in range(1, 13)]
    col_weights = [0.5] + [1] * 12

    if 'selected_wells' not in st.session_state:
        st.session_state.selected_wells = set()

    # Render Headers
    header_cols = st.columns(col_weights)
    for idx, col_num in enumerate(cols):
        header_cols[idx + 1].write(f"**{col_num}**")

    # Render Grid
    for r in rows:
        cols_list = st.columns(col_weights)
        cols_list[0].write(f"**{r}**")
        
        for i, col_name in enumerate(cols):
            well_id = f"{r}{col_name}"
            is_selected = well_id in st.session_state.selected_wells
            
            if cols_list[i+1].button(well_id, key=well_id, type="primary" if is_selected else "secondary"):
                if well_id in st.session_state.selected_wells:
                    st.session_state.selected_wells.remove(well_id)
                else:
                    st.session_state.selected_wells.add(well_id)
                st.rerun()
    
    # Return the sorted list so other parts of the app can use it
    return sorted(list(st.session_state.selected_wells))
