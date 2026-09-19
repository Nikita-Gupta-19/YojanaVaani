import math
from pathlib import Path
from PIL import Image, ImageDraw

DENSITIES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

NAVY_BG = (10, 15, 29, 255)       # #0A0F1D
SAFFRON = (255, 153, 51, 255)     # #FF9933
SAFFRON_GLOW = (255, 153, 51, 60) # Subtle glow
WHITE = (255, 255, 255, 255)
GREEN = (19, 136, 8, 255)         # #138808 Tricolor green
BORDER_COLOR = (45, 62, 100, 255) # Refined navy border

CANVAS_SIZE = 1024

def draw_icon_art(draw: ImageDraw.ImageDraw, size: int):
    scale = size / 1024.0
    
    # Center coordinates
    cx = size / 2.0
    cy = size / 2.0 - (16 * scale)

    # Tricolor subtle top accent bar (inside the icon)
    bar_w = 260 * scale
    bar_h = 10 * scale
    bar_y = cy - (320 * scale)
    draw.rectangle([cx - bar_w / 2, bar_y, cx - bar_w / 6, bar_y + bar_h], fill=SAFFRON)
    draw.rectangle([cx - bar_w / 6, bar_y, cx + bar_w / 6, bar_y + bar_h], fill=WHITE)
    draw.rectangle([cx + bar_w / 6, bar_y, cx + bar_w / 2, bar_y + bar_h], fill=GREEN)

    # Microphone Capsule (Head)
    cap_w = 160 * scale
    cap_h = 280 * scale
    cap_x0 = cx - cap_w / 2.0
    cap_y0 = cy - (160 * scale)
    cap_x1 = cx + cap_w / 2.0
    cap_y1 = cap_y0 + cap_h
    draw.rounded_rectangle([cap_x0, cap_y0, cap_x1, cap_y1], radius=int(cap_w / 2.0), fill=SAFFRON)

    # Microphone grille slits for texture
    slit_w = 70 * scale
    for sy in [cap_y0 + 70 * scale, cap_y0 + 110 * scale, cap_y0 + 150 * scale]:
        draw.line([cx - slit_w / 2, sy, cx + slit_w / 2, sy], fill=NAVY_BG, width=int(8 * scale))

    # U-shaped pickup cradle around the capsule
    cradle_w = 260 * scale
    cradle_h = 260 * scale
    cradle_x0 = cx - cradle_w / 2.0
    cradle_y0 = cy - (60 * scale)
    cradle_x1 = cx + cradle_w / 2.0
    cradle_y1 = cradle_y0 + cradle_h
    cradle_thickness = int(24 * scale)

    # Arc for cradle (from 0 to 180 degrees)
    draw.arc([cradle_x0, cradle_y0, cradle_x1, cradle_y1], start=0, end=180, fill=SAFFRON, width=cradle_thickness)
    # Cradle vertical tips
    tip_len = 50 * scale
    draw.line([cradle_x0 + cradle_thickness / 2, cradle_y0 + cradle_h / 2, cradle_x0 + cradle_thickness / 2, cradle_y0 + cradle_h / 2 - tip_len], fill=SAFFRON, width=cradle_thickness)
    draw.line([cradle_x1 - cradle_thickness / 2, cradle_y0 + cradle_h / 2, cradle_x1 - cradle_thickness / 2, cradle_y0 + cradle_h / 2 - tip_len], fill=SAFFRON, width=cradle_thickness)

    # Stem
    stem_top = cradle_y0 + cradle_h
    stem_bottom = stem_top + (90 * scale)
    draw.line([cx, stem_top, cx, stem_bottom], fill=SAFFRON, width=cradle_thickness)

    # Base
    base_w = 200 * scale
    base_h = cradle_thickness
    draw.rounded_rectangle([cx - base_w / 2, stem_bottom, cx + base_w / 2, stem_bottom + base_h], radius=int(base_h / 2), fill=SAFFRON)

    # Acoustic wave arcs (Voice / Vaani)
    wave_thickness = int(16 * scale)
    # Left inner wave
    draw.arc([cx - (340 * scale), cy - (150 * scale), cx - (200 * scale), cy + (100 * scale)], start=115, end=245, fill=SAFFRON, width=wave_thickness)
    # Right inner wave
    draw.arc([cx + (200 * scale), cy - (150 * scale), cx + (340 * scale), cy + (100 * scale)], start=295, end=65, fill=SAFFRON, width=wave_thickness)

    # Left outer wave
    draw.arc([cx - (420 * scale), cy - (200 * scale), cx - (240 * scale), cy + (150 * scale)], start=125, end=235, fill=SAFFRON, width=wave_thickness)
    # Right outer wave
    draw.arc([cx + (240 * scale), cy - (200 * scale), cx + (420 * scale), cy + (150 * scale)], start=305, end=55, fill=SAFFRON, width=wave_thickness)

def generate_square_icon(size: int) -> Image.Image:
    # High-res canvas
    img = Image.new('RGBA', (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rect background
    margin = 32
    r = 200
    draw.rounded_rectangle([margin, margin, CANVAS_SIZE - margin, CANVAS_SIZE - margin], radius=r, fill=NAVY_BG, outline=BORDER_COLOR, width=12)

    draw_icon_art(draw, CANVAS_SIZE)
    return img.resize((size, size), Image.Resampling.LANCZOS)

def generate_round_icon(size: int) -> Image.Image:
    img = Image.new('RGBA', (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 32
    draw.ellipse([margin, margin, CANVAS_SIZE - margin, CANVAS_SIZE - margin], fill=NAVY_BG, outline=BORDER_COLOR, width=12)

    draw_icon_art(draw, CANVAS_SIZE)
    return img.resize((size, size), Image.Resampling.LANCZOS)

def main():
    res_dir = Path('/Users/nikita/Documents/YojanaVaani/mobile/android/app/src/main/res')
    for folder, size in DENSITIES.items():
        folder_path = res_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        sq_img = generate_square_icon(size)
        sq_path = folder_path / 'ic_launcher.png'
        sq_img.save(sq_path, 'PNG')
        
        rd_img = generate_round_icon(size)
        rd_path = folder_path / 'ic_launcher_round.png'
        rd_img.save(rd_path, 'PNG')
        
        print(f"Generated {folder}: {sq_path.name} & {rd_path.name} ({size}x{size}px)")

if __name__ == '__main__':
    main()
