"""Generate original CaneSense AI brand assets: logo SVGs, favicon PNG, social preview, light hero/thumbnails."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
BRAND, IMAGES = ROOT / "assets" / "brand", ROOT / "assets" / "images"
BRAND.mkdir(parents=True, exist_ok=True)

MARK = ('<rect width="64" height="64" rx="15" fill="#14432F"/>'
        '<path d="M32 10c8 10 13 17 13 24a13 13 0 0 1-26 0c0-7 5-14 13-24z" fill="#B7E36A"/>'
        '<path d="M32 50V30m0 8c-5-1-8-4-9-9m9 3c5-1 8-4 9-9" stroke="#14432F" stroke-width="3" stroke-linecap="round" fill="none"/>')

(BRAND / "logo_mark.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{MARK}</svg>', encoding="utf-8")
(BRAND / "logo_wordmark.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 64"><g>' + MARK + '</g>'
    '<text x="76" y="30" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="23" font-weight="700" fill="#FFFFFF">CaneSense <tspan fill="#B7E36A">AI</tspan></text>'
    '<text x="76" y="48" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="10.5" letter-spacing="1.2" fill="#A8BDB2">PRECISION IRRIGATION</text></svg>', encoding="utf-8")


def mark_png(size: int) -> Image.Image:
    s = 4
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = size * s / 64
    d.rounded_rectangle([0, 0, 64 * k, 64 * k], radius=15 * k, fill="#14432F")
    # drop: circle + triangle top
    d.ellipse([19 * k, 21 * k, 45 * k, 47 * k], fill="#B7E36A")
    d.polygon([(32 * k, 10 * k), (21.5 * k, 31 * k), (42.5 * k, 31 * k)], fill="#B7E36A")
    d.line([(32 * k, 50 * k), (32 * k, 30 * k)], fill="#14432F", width=int(3 * k))
    d.line([(32 * k, 38 * k), (23 * k, 29 * k)], fill="#14432F", width=int(3 * k))
    d.line([(32 * k, 35 * k), (41 * k, 26 * k)], fill="#14432F", width=int(3 * k))
    return im.resize((size, size), Image.LANCZOS)


mark_png(192).save(BRAND / "favicon.png")
mark_png(32).save(BRAND / "favicon-32.png")


def font(size, bold=False):
    for n in (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


# Social preview 1200x630 from the hero photograph
hero = Image.open(IMAGES / "hero_sugarcane.jpg").convert("RGB")
w, h = hero.size
crop = hero.crop((0, int(h * 0.15), w, int(h * 0.15) + int(w * 630 / 1200))).resize((1200, 630), Image.LANCZOS)
ov = Image.new("RGBA", (1200, 630), (0, 0, 0, 0))
od = ImageDraw.Draw(ov)
for x in range(1200):
    a = int(235 * max(0, 1 - x / 900))
    od.line([(x, 0), (x, 630)], fill=(14, 52, 36, a))
img = Image.alpha_composite(crop.convert("RGBA"), ov)
img.alpha_composite(mark_png(84), (64, 64))
d = ImageDraw.Draw(img)
d.text((166, 74), "CaneSense AI", font=font(40, True), fill="white")
d.text((166, 122), "PRECISION IRRIGATION INTELLIGENCE", font=font(18), fill="#B7E36A")
d.text((64, 300), "Make every drop count.", font=font(64, True), fill="white")
d.text((64, 396), "AI-assisted irrigation planning for smarter,\nmore sustainable sugarcane farming.", font=font(28), fill="#E7EFE9", spacing=8)
d.text((64, 560), "Demo with synthetic data", font=font(20), fill="#B7E36A")
img.convert("RGB").save(BRAND / "social_preview.jpg", quality=85, optimize=True)

# Lighter hero for the app, plus small header crops
hero.resize((1500, int(1500 * h / w)), Image.LANCZOS).save(IMAGES / "hero_sugarcane_1500.jpg", quality=72, optimize=True, progressive=True)
for src, dst in [("field_tamilnadu.jpg", "field_header.jpg"), ("irrigation_nrcs.jpg", "irrigation_header.jpg")]:
    im = Image.open(IMAGES / src).convert("RGB")
    iw, ih = im.size
    im.crop((0, int(ih * 0.25), iw, int(ih * 0.25) + int(iw / 5))).resize((1200, 240), Image.LANCZOS).save(IMAGES / dst, quality=70, optimize=True)
print("brand assets written")
