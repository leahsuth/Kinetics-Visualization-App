import cairosvg

def _svg_to_png(svg_str: str) -> bytes:
    return cairosvg.svg2png(bytestring=svg_str.encode())
