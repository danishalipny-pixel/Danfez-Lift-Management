import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_SRC = os.path.join(ROOT, "frontend", "assets", "icons", "icon-512.png")
RES_DIR = os.path.join(ROOT, "android", "app", "src", "main", "res")

# Load source icon
if not os.path.exists(ICON_SRC):
    print(f"Error: {ICON_SRC} not found")
    exit(1)

base_img = Image.open(ICON_SRC).convert("RGBA")

# Mipmap dimensions
# (folder, launcher_size, foreground_size)
MIPMAPS = [
    ("mipmap-mdpi", 48, 108),
    ("mipmap-hdpi", 72, 162),
    ("mipmap-xhdpi", 96, 216),
    ("mipmap-xxhdpi", 144, 324),
    ("mipmap-xxxhdpi", 192, 432),
]

def make_round(img):
    """Create circular mask for round launcher icons."""
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
    result = img.copy()
    result.putalpha(mask)
    return result

def make_foreground(img, target_size):
    """Place icon centered inside target canvas with padding for adaptive icon."""
    fg = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    # Icon inside foreground takes ~65% of size so it doesn't get clipped by adaptive mask
    inner_size = int(target_size * 0.65)
    resized_icon = img.resize((inner_size, inner_size), Image.Resampling.LANCZOS)
    offset = (target_size - inner_size) // 2
    fg.paste(resized_icon, (offset, offset), resized_icon)
    return fg

# Generate mipmap icons
for folder, size, fg_size in MIPMAPS:
    target_dir = os.path.join(RES_DIR, folder)
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. Standard square/adaptive icon
    sq_icon = base_img.resize((size, size), Image.Resampling.LANCZOS)
    sq_icon.save(os.path.join(target_dir, "ic_launcher.png"), "PNG")
    
    # 2. Round icon
    round_icon = make_round(sq_icon)
    round_icon.save(os.path.join(target_dir, "ic_launcher_round.png"), "PNG")
    
    # 3. Foreground icon for adaptive icons
    fg_icon = make_foreground(base_img, fg_size)
    fg_icon.save(os.path.join(target_dir, "ic_launcher_foreground.png"), "PNG")

print("[OK] Generated Android launcher and adaptive icons.")

# Generate Splash Screen
# Splash dimensions for port and land
SPLASH_SIZES = [
    ("drawable", 480, 800),
    ("drawable-port-mdpi", 320, 480),
    ("drawable-port-hdpi", 480, 800),
    ("drawable-port-xhdpi", 720, 1280),
    ("drawable-port-xxhdpi", 960, 1600),
    ("drawable-port-xxxhdpi", 1280, 1920),
    ("drawable-land-mdpi", 480, 320),
    ("drawable-land-hdpi", 800, 480),
    ("drawable-land-xhdpi", 1280, 720),
    ("drawable-land-xxhdpi", 1600, 960),
    ("drawable-land-xxxhdpi", 1920, 1280),
]

NAVY = (7, 22, 43, 255) # #07162B

for folder, w, h in SPLASH_SIZES:
    target_dir = os.path.join(RES_DIR, folder)
    os.makedirs(target_dir, exist_ok=True)
    splash = Image.new("RGBA", (w, h), NAVY)
    
    # Place logo centered
    logo_size = min(w, h) // 3
    logo_resized = base_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    pos_x = (w - logo_size) // 2
    pos_y = (h - logo_size) // 2
    splash.paste(logo_resized, (pos_x, pos_y), logo_resized)
    splash.save(os.path.join(target_dir, "splash.png"), "PNG")

print("[OK] Generated Android splash screens.")
