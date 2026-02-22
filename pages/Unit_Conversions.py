import streamlit as st

st.logo(image='assets/Merck_Logo.png')
st.write("# Unit Conversions")
st.markdown(
    "Convert common lab units across length, mass, volume, and temperature."
)


def convert_temperature(value, from_unit, to_unit):
    if from_unit == to_unit:
        return value
    if from_unit == "C":
        c_value = value
    elif from_unit == "F":
        c_value = (value - 32) * 5 / 9
    else:
        c_value = value - 273.15

    if to_unit == "C":
        return c_value
    if to_unit == "F":
        return c_value * 9 / 5 + 32
    return c_value + 273.15


UNIT_GROUPS = {
    "Length": {
        "base": "m",
        "units": {
            "nm": 1e-9,
            "um": 1e-6,
            "mm": 1e-3,
            "cm": 1e-2,
            "m": 1.0,
            "km": 1e3,
            "in": 0.0254,
            "ft": 0.3048,
        },
    },
    "Mass": {
        "base": "g",
        "units": {
            "ug": 1e-6,
            "mg": 1e-3,
            "g": 1.0,
            "kg": 1e3,
            "lb": 453.59237,
        },
    },
    "Volume": {
        "base": "L",
        "units": {
            "uL": 1e-6,
            "mL": 1e-3,
            "L": 1.0,
            "gal": 3.785411784,
        },
    },
    "Temperature": {
        "units": ["C", "F", "K"],
    },
}

category = st.selectbox("Conversion type", list(UNIT_GROUPS.keys()))
value = st.number_input("Value", value=1.0, format="%.6f")

col_left, col_right = st.columns(2)
if category == "Temperature":
    with col_left:
        from_unit = st.selectbox("From", UNIT_GROUPS[category]["units"], index=0)
    with col_right:
        to_unit = st.selectbox("To", UNIT_GROUPS[category]["units"], index=1)
    result = convert_temperature(value, from_unit, to_unit)
else:
    units = UNIT_GROUPS[category]["units"]
    unit_list = list(units.keys())
    with col_left:
        from_unit = st.selectbox("From", unit_list, index=0)
    with col_right:
        to_unit = st.selectbox("To", unit_list, index=1)
    base_value = value * units[from_unit]
    result = base_value / units[to_unit]

st.metric(
    label=f"{value:g} {from_unit} in {to_unit}",
    value=f"{result:.6g} {to_unit}",
)
