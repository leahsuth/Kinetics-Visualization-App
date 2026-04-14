import os

def get_assets(file_path):
    """Reads files from the same directory as the caller script."""
    if not os.path.exists(file_path):
        return None

    html_path = f"{file_path}/index.html" 
    if os.path.exists(html_path):
        with open(html_path, "r") as file:
            html = file.read()
    else:
        html = None

    css_path = f"{file_path}/index.css"
    if os.path.exists(css_path)
        with open(css_path, "r") as file:
            css = file.read()
    else:
        css = None


    js_path = f"{file_path}/index.js"
    if os.path.exists(js_path)
        with open(js_path, "r") as file:
            js = file.read()
    else:
        js = None

    return html, css, js
