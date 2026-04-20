import streamlit as st

def excess(r, s):
    top = abs(r - s)
    bottom = r + s
    return top / bottom * 100

def ee_widget():
    st.header('Enantiomeric Excess Calculator')
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            R = st.number_input("R enantiomer (concentration)", min_value=0.001, value=0.50)

        with col2:
            S = st.number_input("S enantiomer (concentration)", min_value=0.001, value=0.50)

        results = st.container(horizontal=True)

        with results:
            calc = st.button("Calculate EE", type="primary")
            clear = st.button("Clear EE", type="secondary")

        if calc:
            result = excess(R,S) 
            st.write(f"Result: {result}")

        if clear:
            st.write("clear pressed")
