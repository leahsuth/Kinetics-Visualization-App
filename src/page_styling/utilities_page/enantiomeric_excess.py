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
            R = st.number_input("R enantiomer (concentration)", min_value=0.001, value=50.0)

        with col2:
            S = st.number_input("S enantiomer (concentration)", min_value=0.001, value=50.0)

        results = st.container(horizontal=True)
        if (S + R) != 100:
            st.error("S and R must sum to 100")
        else:
            result = excess(R,S) 
            results.write(f"## Result: {result}%")
