import os

def get_assets(file_path):
    """Reads files from the same directory as the caller script."""

    html_path = f"{file_path}/index.html" 
    if os.path.exists(html_path):
        with open(html_path, "r") as file:
            html = file.read()
    else:
        html = None

    css_path = f"{file_path}/index.css"
    if os.path.exists(css_path):
        with open(css_path, "r") as file:
            css = file.read()
    else:
        css = None

    return html, css
