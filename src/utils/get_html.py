import streamlit as st

def get_assets(file_path):
    """Reads files from the same directory as the caller script."""
    st.write(file_path)
    with open(f"{file_path}/index.html", "r") as file:
        html = file.read()

    with open(f"{file_path}/index.css", "r") as file:
        css = file.read()

    return html, css
