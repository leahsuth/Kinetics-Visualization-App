import streamlit as st

def de_excess(r, s):
    top = abs(r - s)
    bottom = r + s
    return top / bottom * 100

def de_widget():
    st.header('Diasteriometric Excess Calculator')
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            R = st.number_input("Diastereomer 1 (concentration)", min_value=0.001, value=50)

        with col2:
            S = st.number_input("Diastereomer 2 (concentration)", min_value=0.001, value=50)

        results = st.container(horizontal=True)
        if (S + R) != 100:
            st.error("S and R must sum to 100")
            st.stop()

        result = de_excess(R,S) 
        results.write(f"## Result: {result}%")
