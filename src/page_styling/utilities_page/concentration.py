import streamlit as st

def concentration_calc(mw, mass, volume):
    moles = mass / mw
    conc = moles / volume
    return conc

def mass_calc(conc, mw, volume):
    moles = conc * volume
    mass = moles * mw
    return mass

def volume_calc(mass, mw, conc):
    moles = mass / mw
    volume = moles / conc
    return volume

def concentration_from_mass_and_volume_widget():
    main_body = st.container(border=True, horizontal=False, width=900)
    main_body.markdown("## Concentration from Mass & Volume")
    main_body.divider()
    with main_body:
        sub_body = st.container(border=False, gap="large", horizontal=True)
        with sub_body:
            mw = st.number_input("Molecular Weight (g/mol)", min_value=0.0, step=1.0, format="%0.4f", value=1.0)
            mass = st.number_input("Mass (g)", min_value=0.0, step=1.0, format="%0.4f", value=1.0)
            volume = st.number_input("Volume (mL)", min_value=0.0,step=1.0, format="%0.4f", value=1.0)

        if any(value <= 0 for value in [mw,mass,volume]):
            return

        conc = concentration_calc(mw,mass,volume)
    main_body.markdown(f"#### Concentration :arrow_right: {conc:.4f} mol / mL") 

def mass_from_volume_and_concentration_widget():
    main_body = st.container(border=True, horizontal=False, width=900)
    main_body.markdown("## Mass from Volume and Concentration")
    main_body.divider()
    with main_body:
        sub_body = st.container(border=False, gap="large", horizontal=True)
        with sub_body:
            mw = st.number_input("Molecular Weight (g/mol)", min_value=0.0, step=1.0, format="%0.4f", value=1.0)
            conc = st.number_input("Molarity (mol/mL)", min_value=0.0, step=1.0, format="%0.4f", value=1.0)
            volume = st.number_input("Volume (mL)", min_value=0.0, step=1.0, format="%0.4f", value=1.0)

        if any(value <= 0 for value in [mw,conc,volume]):
            return
    mass = mass_calc(conc, mw, volume)
        
    main_body.markdown(f"#### Mass :arrow_right: {mass:.4f} grams")


def volume_from_mass_and_concentration_widget():
    main_body = st.container(border=True, horizontal=False, width=900)
    main_body.markdown("## Volume from Mass and Concentration")
    main_body.divider()
    with main_body:
        sub_body = st.container(border=False, gap="large", horizontal=True)
        with sub_body:
            mw = st.number_input("Molecular Weight (g/mol)", min_value=0.0, step=1.0, format="%0.4f", value=1.0)
            conc = st.number_input("Molarity (mol/mL)", min_value=0.0, step=1.0, format="%0.4f", value=1.0)
            mass = st.number_input("Mass (g)", min_value=0.0, step=1.0, format="%0.4f", value=1.0)

        if any(value <= 0 for value in [mw,conc,mass]):
            return
    volume = volume_calc(mass, mw, conc)
        
    main_body.markdown(f"#### Volume: :arrow_right: {volume:.4f} mL")

def main_concentration_widget():
    options = ['mass', 'volume', 'concentration']
    selection = st.radio("Select what variable to solve for", options)

    if selection == 'mass':
        mass_from_volume_and_concentration_widget()
    elif selection == 'volume':
        volume_from_mass_and_concentration_widget()
    else:
        concentration_from_mass_and_volume_widget()

