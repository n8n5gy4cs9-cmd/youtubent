"""Generate ALL sprites/icons with Pillow. Run: python tools/make_sprites.py
Outputs: assets/sprites/*.png, assets/app/icon.png|icns|ico, assets/app/logo.png, assets/illustrations/*.png
Icons are drawn on a 64-grid, supersampled 8x for smooth edges."""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent / "assets"
S = 8  # supersample
G = 64  # design grid
LIGHT = (230, 231, 234, 255)
ACCENT = (255, 77, 94, 255)
DIM = (120, 122, 130, 255)
W = 5  # stroke width in grid units


class Pen:
    def __init__(self, color):
        self.im = Image.new("RGBA", (G * S, G * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.c = color

    def p(self, v):
        return [(x * S, y * S) if isinstance(v[0], (int, float)) is False else v for x, y in v] if False else None

    @staticmethod
    def sc(pts):
        return [(x * S, y * S) for x, y in pts]

    def line(self, pts, w=W):
        pts = self.sc(pts)
        self.d.line(pts, fill=self.c, width=int(w * S), joint="curve")
        for x, y in (pts[0], pts[-1]):  # round caps
            r = w * S / 2
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=self.c)

    def rect(self, box, r=4, fill=False, w=W):
        b = [v * S for v in box]
        if fill:
            self.d.rounded_rectangle(b, radius=r * S, fill=self.c)
        else:
            self.d.rounded_rectangle(b, radius=r * S, outline=self.c, width=int(w * S))

    def ellipse(self, box, fill=False, w=W):
        b = [v * S for v in box]
        if fill:
            self.d.ellipse(b, fill=self.c)
        else:
            self.d.ellipse(b, outline=self.c, width=int(w * S))

    def poly(self, pts):
        self.d.polygon(self.sc(pts), fill=self.c)

    def arc(self, box, a0, a1, w=W):
        self.d.arc([v * S for v in box], a0, a1, fill=self.c, width=int(w * S))

    def out(self, size=G):
        return self.im.resize((size, size), Image.LANCZOS)


def sparkle(p, cx, cy, r):
    pts = []
    for i in range(8):
        a = i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.28
        pts.append((cx + rr * math.sin(a), cy - rr * math.cos(a)))
    p.poly(pts)


# ---- icon drawers: fn(p) on a 64 grid ----
def i_load(p):
    p.line([(32, 10), (32, 40)]); p.line([(20, 29), (32, 41), (44, 29)]); p.line([(12, 52), (52, 52)])
def i_generate(p):
    sparkle(p, 26, 34, 20); sparkle(p, 49, 14, 9); sparkle(p, 50, 48, 7)
def i_add(p):
    p.line([(32, 12), (32, 52)]); p.line([(12, 32), (52, 32)])
def i_delete(p):
    p.line([(12, 18), (52, 18)]); p.line([(25, 18), (25, 11), (39, 11), (39, 18)])
    p.line([(16, 18), (19, 54), (45, 54), (48, 18)]); p.line([(27, 28), (27, 44)], 4); p.line([(37, 28), (37, 44)], 4)
def i_play(p):
    p.poly([(18, 10), (18, 54), (54, 32)])
def i_pause(p):
    p.rect((14, 10, 26, 54), 3, True); p.rect((38, 10, 50, 54), 3, True)
def i_prev(p):
    p.rect((12, 12, 18, 52), 2, True); p.poly([(52, 12), (52, 52), (22, 32)])
def i_next(p):
    p.rect((46, 12, 52, 52), 2, True); p.poly([(12, 12), (12, 52), (42, 32)])
def i_export(p):
    p.line([(32, 40), (32, 8)]); p.line([(20, 20), (32, 8), (44, 20)]); p.line([(14, 30), (14, 54), (50, 54), (50, 30)])
def i_save(p):
    p.rect((10, 10, 54, 54), 6); p.line([(20, 10), (20, 24), (42, 24), (42, 10)], 4); p.rect((20, 38, 44, 54), 2, False, 4)
def i_open(p):
    p.line([(8, 20), (8, 52), (50, 52), (56, 30), (22, 30), (16, 52)], 4.5); p.line([(8, 20), (8, 14), (24, 14), (28, 20), (46, 20), (46, 30)], 4.5)
def i_copy(p):
    p.rect((20, 20, 52, 54), 5); p.line([(14, 40), (12, 40), (12, 10), (40, 10), (40, 14)], 4.5)
def i_shuffle(p):
    p.line([(8, 20), (20, 20), (40, 44), (54, 44)]); p.line([(8, 44), (20, 44), (28, 33)]); p.line([(36, 27), (40, 20), (54, 20)])
    p.line([(47, 13), (55, 20), (47, 27)], 4); p.line([(47, 37), (55, 44), (47, 51)], 4)
def i_even(p):
    for x in (12, 26, 40, 54):
        p.line([(x, 14), (x, 50)], 5)
def i_image(p):
    p.rect((8, 12, 56, 52), 6); p.ellipse((18, 20, 28, 30), True); p.line([(12, 48), (26, 34), (36, 44), (44, 36), (54, 46)], 4.5)
def i_pdf(p):
    p.line([(14, 8), (14, 56), (50, 56), (50, 22), (36, 8), (14, 8)], 4.5); p.line([(36, 8), (36, 22), (50, 22)], 4)
    p.line([(22, 34), (42, 34)], 4); p.line([(22, 44), (42, 44)], 4)
def i_caption(p):
    p.line([(10, 12), (54, 12), (54, 42), (30, 42), (18, 54), (18, 42), (10, 42), (10, 12)], 4.5); p.line([(20, 24), (44, 24)], 4); p.line([(20, 32), (36, 32)], 4)
def i_clock(p):
    p.ellipse((8, 8, 56, 56)); p.line([(32, 18), (32, 32), (42, 38)], 4.5)
def i_reorder(p):
    for y in (18, 32, 46):
        p.line([(12, y), (52, y)], 5)
def i_check(p):
    p.line([(12, 34), (26, 48), (53, 17)], 6)
def i_close(p):
    p.line([(14, 14), (50, 50)], 6); p.line([(50, 14), (14, 50)], 6)
def i_warning(p):
    p.line([(32, 8), (58, 52), (6, 52), (32, 8)], 4.5); p.line([(32, 24), (32, 38)], 4.5); p.ellipse((29.5, 42, 34.5, 47), True)
def i_folder(p):
    p.line([(6, 14), (6, 52), (58, 52), (58, 22), (30, 22), (24, 14), (6, 14)], 4.5)
def i_zoom(p):
    p.ellipse((8, 8, 42, 42)); p.line([(37, 37), (55, 55)], 6)
def i_film(p):
    p.rect((8, 8, 56, 56), 6); p.line([(20, 8), (20, 56)], 3.5); p.line([(44, 8), (44, 56)], 3.5)
    for y in (18, 32, 46):
        p.rect((11, y - 2, 16, y + 2), 1, True); p.rect((48, y - 2, 53, y + 2), 1, True)
def i_pin(p):
    p.poly([(32, 56), (14, 24), (50, 24)]); p.ellipse((14, 6, 50, 42), True)
def i_dice(p):
    p.rect((8, 8, 56, 56), 9)
    for x, y in ((22, 22), (42, 22), (32, 32), (22, 42), (42, 42)):
        p.ellipse((x - 3.5, y - 3.5, x + 3.5, y + 3.5), True)
def i_laugh(p):
    p.ellipse((8, 8, 56, 56)); p.arc((18, 24, 46, 50), 0, 180, 4.5); p.line([(21, 25), (27, 22)], 4); p.line([(43, 25), (37, 22)], 4)
def i_user_grid(p):
    for x in (10, 36):
        for y in (10, 36):
            p.rect((x, y, x + 18, y + 18), 4)

ICONS = {k[2:]: v for k, v in globals().items() if k.startswith("i_")}


def make_icons():
    out = ROOT / "sprites"; out.mkdir(parents=True, exist_ok=True)
    for name, fn in ICONS.items():
        for suffix, col in (("", LIGHT), ("_accent", ACCENT), ("_dim", DIM)):
            p = Pen(col); fn(p); p.out(64).save(out / f"{name}{suffix}.png")
    print(f"{len(ICONS)*3} icon sprites")


def font(size, bold=True):
    for n in ("Helvetica.ttc", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def app_icon(size=1024):
    S2 = 2
    N = size * S2
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    m = int(N * 0.06)
    # squircle bg with vertical gradient
    grad = Image.new("RGBA", (N, N))
    gd = ImageDraw.Draw(grad)
    for y in range(N):
        t = y / N
        gd.line([(0, y), (N, y)], fill=(int(46 - 20 * t), int(47 - 20 * t), int(54 - 22 * t), 255))
    mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(mask).rounded_rectangle((m, m, N - m, N - m), radius=int(N * 0.22), fill=255)
    im.paste(grad, (0, 0), mask)
    # three storyboard frames, last one accent with play triangle
    fw, fh = int(N * 0.22), int(N * 0.30)
    gap = int(N * 0.04)
    x0 = (N - (3 * fw + 2 * gap)) // 2
    y0 = int(N * 0.30)
    for i in range(3):
        x = x0 + i * (fw + gap)
        col = ACCENT if i == 2 else (230, 231, 234, 255)
        d.rounded_rectangle((x, y0, x + fw, y0 + fh), radius=int(N * 0.03), fill=col)
        if i == 2:
            cx, cy, r = x + fw // 2, y0 + fh // 2, int(fw * 0.22)
            d.polygon([(cx - r * 0.7, cy - r), (cx - r * 0.7, cy + r), (cx + r * 1.1, cy)], fill=(255, 255, 255, 255))
        else:
            d.rounded_rectangle((x + fw * 0.15, y0 + fh * 0.62, x + fw * (0.85 - 0.2 * i), y0 + fh * 0.74), radius=int(N * 0.01), fill=(90, 92, 100, 255))
            d.ellipse((x + fw * 0.2, y0 + fh * 0.15, x + fw * 0.45, y0 + fh * 0.15 + fw * 0.25), fill=(90, 92, 100, 255))
    # timeline under frames with markers
    ty = y0 + fh + int(N * 0.09)
    d.rounded_rectangle((x0, ty, x0 + 3 * fw + 2 * gap, ty + int(N * 0.02)), radius=int(N * 0.01), fill=(95, 97, 105, 255))
    for i in range(3):
        cx = x0 + fw // 2 + i * (fw + gap)
        r = int(N * 0.028)
        d.ellipse((cx - r, ty + int(N * 0.01) - r, cx + r, ty + int(N * 0.01) + r), fill=ACCENT if i == 2 else (230, 231, 234, 255))
    return im.resize((size, size), Image.LANCZOS)


def make_app():
    out = ROOT / "app"; out.mkdir(parents=True, exist_ok=True)
    icon = app_icon()
    icon.save(out / "icon.png")
    icon.save(out / "icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    try:
        icon.save(out / "icon.icns")
    except Exception as e:
        print("icns skipped:", e)
    # logo wordmark
    f = font(64)
    logo = Image.new("RGBA", (560, 96), (0, 0, 0, 0))
    ld = ImageDraw.Draw(logo)
    logo.paste(icon.resize((80, 80), Image.LANCZOS), (4, 8))
    ld.text((100, 14), "Youtuben't", font=f, fill=LIGHT)
    x = 100 + ld.textlength("Youtuben", font=f)
    ld.text((x, 14), "'t", font=f, fill=ACCENT)
    logo.save(out / "logo.png")
    logo.resize((280, 48), Image.LANCZOS).save(out / "logo_small.png")
    print("app icon + logo")


def make_extras():
    sp = ROOT / "sprites"; il = ROOT / "illustrations"; il.mkdir(parents=True, exist_ok=True)
    # spinner: 8 frames
    for f in range(8):
        p = Pen(LIGHT)
        for i in range(8):
            a = 2 * math.pi * i / 8
            alpha = int(255 * (((i - f) % 8) + 1) / 8)
            col = (255, 77, 94, alpha)
            pen = Pen(col)
            x0, y0 = 32 + 20 * math.sin(a), 32 - 20 * math.cos(a)
            x1, y1 = 32 + 28 * math.sin(a), 32 - 28 * math.cos(a)
            pen.line([(x0, y0), (x1, y1)], 5)
            p.im = Image.alpha_composite(p.im, pen.im)
        p.out(64).save(sp / f"spinner_{f}.png")
    # timeline marker + playhead (small, drawn at 2x)
    m = Image.new("RGBA", (S * 24, S * 32), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.polygon([(12 * S, 31 * S), (3 * S, 14 * S), (21 * S, 14 * S)], fill=ACCENT)
    d.ellipse((1 * S, 1 * S, 23 * S, 23 * S), fill=ACCENT)
    d.ellipse((8 * S, 8 * S, 16 * S, 16 * S), fill=(27, 28, 31, 255))
    m.resize((24, 32), Image.LANCZOS).save(sp / "marker.png")
    ph = Image.new("RGBA", (S * 16, S * 32), (0, 0, 0, 0)); d = ImageDraw.Draw(ph)
    d.polygon([(1 * S, 1 * S), (15 * S, 1 * S), (15 * S, 10 * S), (8 * S, 17 * S), (1 * S, 10 * S)], fill=LIGHT)
    ph.resize((16, 32), Image.LANCZOS).save(sp / "playhead.png")
    # sticker sparkles
    s = Pen(ACCENT); sparkle(s, 30, 34, 26); sparkle(s, 52, 12, 10); s.out(64).save(sp / "sticker_sparkle.png")
    # empty-state illustration (400x240)
    W2, H2 = 400 * 2, 240 * 2
    im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cols = [(58, 60, 68, 255), (70, 72, 82, 255), (255, 77, 94, 255)]
    for i, c in enumerate(cols):
        x = 70 + i * 90
        y = 60 + (i % 2) * 20 + (2 - i) * -4
        d.rounded_rectangle((x * 2, y * 2, (x + 110) * 2, (y + 80) * 2), radius=24, fill=c)
        if i == 2:
            d.polygon([((x + 44) * 2, (y + 22) * 2), ((x + 44) * 2, (y + 58) * 2), ((x + 74) * 2, (y + 40) * 2)], fill=(255, 255, 255, 255))
        else:
            d.ellipse(((x + 16) * 2, (y + 14) * 2, (x + 40) * 2, (y + 38) * 2), fill=(100, 102, 112, 255))
            d.rounded_rectangle(((x + 16) * 2, (y + 52) * 2, (x + 90 - i * 20) * 2, (y + 60) * 2), radius=8, fill=(100, 102, 112, 255))
    d.line([(70 * 2, 190 * 2), (330 * 2, 190 * 2)], fill=(90, 92, 100, 255), width=8)
    for i in range(3):
        cx = (125 + i * 90) * 2
        d.ellipse((cx - 14, 190 * 2 - 14, cx + 14, 190 * 2 + 14), fill=ACCENT if i == 2 else LIGHT)
    im.resize((400, 240), Image.LANCZOS).save(il / "empty.png")
    print("spinner, marker, playhead, sticker, empty-state")


if __name__ == "__main__":
    make_icons(); make_app(); make_extras()
