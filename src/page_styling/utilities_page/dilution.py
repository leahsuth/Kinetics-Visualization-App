import streamlit as st
from src.page_styling.utilities_page.dilution_scheme_comp.scheme import render_card

def dilution_step(
    stock_conc,
    dilution_factor,
    total_vol,
    num_steps
):
    try:
        transfer_vol = total_vol / dilution_factor
        diluent_vol = total_vol - transfer_vol
        return transfer_vol, diluent_vol
    except ValueError:
        st.error("Invaid Input for dilution calculations")


def dilution_widget():
    st.write('# Serial Dilutions')
    main_body = st.container(border=True, horizontal=False, width=900)
    with main_body:
        header_info = st.container(border=False, horizontal=True)
        header_info_2 = st.container(border=False, horizontal=True)
        with header_info:
            number_of_dilutions = st.number_input("Number of Dilutions", 1, value=1)
            stock_conc = st.number_input("Stock Concentration", 0, value=1)
            dilution_factor = st.number_input("Dilution Factor")
            final_volume = st.number_input("Final Volume", 0)
        with header_info_2:
            st.write("hello world")

        st.divider()
        dilution_body = st.container(border=False, horizontal=False)
        with dilution_body:
            render_card("foo", "Bar")
            for x in range(number_of_dilutions):
                st.write(f"Dilution Number {x+1}")
