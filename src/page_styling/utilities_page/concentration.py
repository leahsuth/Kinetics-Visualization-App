import streamlit as st

def concentration_calc(mw, mass, volume):
    moles = mass / mw
    molarity = moles / volume
    return molarity

def mass_calc(conc, mw, volume):
    pass

def volume_calc(mass, mw, conc):
    pass

def concentration_widget():
    main_body = st.container(border=True, horizontal=False)
    main_body.markdown("## Hello world")
    with main_body:
        sub_body = st.container(border=False, gap="large", horizontal=True)
        with sub_body:
            mw = st.number_input("Molecular Weight", min_value=0)
            mass = st.number_input("Mass (g)", min_value=0)
            volume = st.number_input("Volume (ml)", min_value=0)

        if any(value <= 0 for value in [mw,mass,volume]):
            return

        conc = concentration_calc(mw,mass,volume)
        st.markdown(conc)

