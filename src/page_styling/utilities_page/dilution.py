import streamlit as st
import pandas as pd

def calculate_serial_dilution(stock_conc, target_conc, num_steps, total_vol):
    if stock_conc <= target_conc:
        st.error("Stock concentration must be greater than target concentration.")
        return None
    
    # Calculate the dilution factor per step
    # C_final = C_stock * (1/DF)^n -> DF = (C_stock/C_target)^(1/n)
    df_per_step = (stock_conc / target_conc) ** (1 / num_steps)
    
    transfer_vol = total_vol / df_per_step
    diluent_vol = total_vol - transfer_vol
    
    data = []
    current_conc = stock_conc
    
    for i in range(1, num_steps + 1):
        next_conc = current_conc / df_per_step
        data.append({
            "Step": i,
            "Source Conc": round(current_conc, 4),
            "Transfer Vol": round(transfer_vol, 2),
            "Diluent Vol": round(diluent_vol, 2),
            "Final Vol": round(total_vol, 2),
            "Resulting Conc": round(next_conc, 4)
        })
        current_conc = next_conc
        
    return pd.DataFrame(data)

def dilution_widget():
    st.header('Serial Dilution Calculator')
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            stock_conc = st.number_input("Stock Concentration", min_value=0.001, value=100.0)
            target_conc = st.number_input("Target Concentration", min_value=0.0001, value=1.0)
        with col2:
            num_steps = st.number_input("Number of Dilutions (Steps)", min_value=1, value=5)
            total_vol = st.number_input("Total Volume per intermediate", min_value=0.1, value=10.0)

        if st.button("Calculate Scheme"):
            df_results = calculate_serial_dilution(stock_conc, target_conc, num_steps, total_vol)
            
            if df_results is not None:
                st.divider()
                st.subheader("Dilution Scheme")
                # Using st.dataframe for a clean, sortable table
                st.dataframe(df_results, use_container_width=True, hide_index=True)
                
                # Summary metrics
                st.info(f"Required Dilution Factor per step: **{round((stock_conc/target_conc)**(1/num_steps), 2)}x**")

