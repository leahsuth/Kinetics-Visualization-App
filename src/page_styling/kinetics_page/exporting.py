import streamlit as st
from src.page_styling.report_generator import generate_report_pdf
from src.parsing.parsing_data import format_download_columns

def export_report(reaction_plot_data, rate_summaries):
    with st.container():
        st.subheader("Export Report")
        try:
            pdf_bytes = generate_report_pdf(
                experiment_setup=st.session_state.get("experiment_setup", {}),
                hplc_file_name=st.session_state.get("hplc_file_name", "-"),
                plot_history=st.session_state.get("kinetics_plot_history", []),
                reaction_plots=reaction_plot_data,
                rate_summaries=rate_summaries,
            )
            st.download_button(
                "Download Report (.pdf)",
                data=pdf_bytes,
                file_name="kinetics_report.pdf",
                mime="application/pdf",
                width="stretch",
                type="primary",
            )
        except Exception as e:
            st.warning(f"PDF export unavailable: {e}")

def export_processed_data_file(df):
    with st.container():
        st.subheader("Download Processed Data File")
        st.caption(
            "HPLC Data file, includes information from the initial input file"
        )
        _hplc_name = st.session_state.get("hplc_file_name") or "hplc_data"
        _stem = _hplc_name.rsplit(".", 1)[0] if "." in _hplc_name else _hplc_name
        download_df = format_download_columns(df)
        _merged_csv = download_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download processed data (.csv)",
            data=_merged_csv,
            file_name=f"{_stem}_processed.csv",
            mime="text/csv",
            width="stretch",
            type="primary",
            key="chemstation_download_processed_csv",
        )

def export_button_layout(df, is_preprocessed, reaction_plot_data, rate_summaries):
    st.divider()
    if is_preprocessed:
        export_report(reaction_plot_data, rate_summaries)
    else:
        with st.container(horizontal=True):
            export_report(reaction_plot_data, rate_summaries)
            export_processed_data_file(df)
