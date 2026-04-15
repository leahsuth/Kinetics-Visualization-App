import streamlit as st

def rate_table_widget(caption, rate, C0, Ce, k, mode):
    st.html(
        f"""
        <div class="rate-table">
            <div class="rate-table-header">{caption}</div>
            <div><b>Rate:</b> {rate:.4f}</div>
            <div><b>C\u2080:</b> {C0:.4f}</div>
            <div><b>C\u2091:</b> {Ce:.4f}</div>
            <div><b>k:</b> {k:.4f}</div>
            <div><b>Mode:</b> {mode}</div>
        </div>
        """
    )
