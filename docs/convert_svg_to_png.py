"""
Convert SVG logos to PNG format for Sphinx documentation.
"""
import os
try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False
    print("cairosvg not installed. Using PIL as fallback.")
    try:
        from PIL import Image
        import io
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False
        print("PIL not installed. Cannot convert SVG to PNG.")

def convert_with_cairosvg(svg_path, png_path, width=200, height=200):
    """Convert SVG to PNG using cairosvg."""
    cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=width, output_height=height)
    print(f"Converted {svg_path} to {png_path} using cairosvg")

def convert_with_pil(svg_path, png_path, width=200, height=200):
    """Convert SVG to PNG using PIL."""
    drawing = svg2rlg(svg_path)
    png_data = renderPM.drawToString(drawing, fmt="PNG")
    img = Image.open(io.BytesIO(png_data))
    img = img.resize((width, height), Image.LANCZOS)
    img.save(png_path)
    print(f"Converted {svg_path} to {png_path} using PIL")

def main():
    """Convert SVG logos to PNG."""
    static_dir = os.path.join(os.path.dirname(__file__), "_static")
    
    svg_files = [
        "logo-light.svg",
        "logo-dark.svg"
    ]
    
    for svg_file in svg_files:
        svg_path = os.path.join(static_dir, svg_file)
        png_path = os.path.join(static_dir, svg_file.replace(".svg", ".png"))
        
        if not os.path.exists(svg_path):
            print(f"SVG file {svg_path} does not exist. Skipping.")
            continue
        
        if HAS_CAIROSVG:
            convert_with_cairosvg(svg_path, png_path)
        elif HAS_PIL:
            convert_with_pil(svg_path, png_path)
        else:
            print("No SVG to PNG converter available. Please install cairosvg or PIL.")

if __name__ == "__main__":
    main()
