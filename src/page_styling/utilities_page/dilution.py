import streamlit as st

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
        with header_info:
            number_of_dilutions = st.number_input("Number of Dilutions", 1, value=1)
            stock_conc = st.number_input("Stock Concentration", 0, value=1)
            dilution_factor = st.number_input("Dilution Factor")
            final_volume = st.number_input("Final Volume", 0)
        dilution_body = st.container(border=False, horizontal=False)
        with dilution_body:
            for x in range(number_of_dilutions):
                st.write(f"Dilution Number {x+1}")
