import streamlit as st
from streamlit.components.v2 import component
from src.utils.get_html import get_assets
from pathlib import Path

PATH = Path(__file__).parent.resolve()
# 1. Register the component with v2
# We define a JS function to handle the dynamic injection
my_v2_card = component(
    "dynamic_card",
    js="""
    export default function(component) {
        const { data, parentElement } = component;
        // Inject the HTML string sent from Python into the main page
        parentElement.innerHTML = data;
    }
    """
)

def render_card(title, value):
    # Load and populate your external HTML
    html, css = get_assets(PATH)
    
    # Replace placeholders
    html_content = html.replace("{{ title }}", title).replace("{{ value }}", value)
    
    # 2. Mount the component with the dynamic data
    my_v2_card(data=html_content)

