"""Draw the Ukraine icon set (iconsets/ukraine.mcm) from scratch, dedicated to the public domain (CC0 1.0).

The OSD is black and white, so the theme comes through shapes: a tryzub (trident) as the home marker
and in the boot logo, the flag's two bands, sunflower battery gauge, wheat ear, heart, stork and drone,
and unit labels in Ukrainian (tiny 3x5 Cyrillic drawn here). Everything else is the OSD Fonts CC0 set.
Slot numbers follow Betaflight's osd_symbols.h.

    uv run iconsets/make_ukraine.py   # writes iconsets/ukraine.mcm and iconsets/ukraine-preview.png
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import make_cc0 as cc0  # noqa: E402
from osdfont.mcm import BLACK, CH, CW, TRANSPARENT, WHITE, mcm_text  # noqa: E402

CYRILLIC = {
    "А": (".#.", "#.#", "###", "#.#", "#.#"), "Б": ("###", "#..", "##.", "#.#", "##."),
    "В": ("##.", "#.#", "##.", "#.#", "##."), "Г": ("###", "#..", "#..", "#..", "#.."),
    "Д": ("##.", "#.#", "#.#", "###", "#.#"), "Е": ("###", "#..", "##.", "#..", "###"),
    "З": ("##.", "..#", ".#.", "..#", "##."),
    "І": ("###", ".#.", ".#.", ".#.", "###"), "Ї": ("#.#", ".#.", ".#.", ".#.", "###"),
    "К": ("#.#", "#.#", "##.", "#.#", "#.#"), "Л": (".##", "#.#", "#.#", "#.#", "#.#"),
    "М": ("#.#", "###", "###", "#.#", "#.#"), "Н": ("#.#", "#.#", "###", "#.#", "#.#"),
    "О": ("###", "#.#", "#.#", "#.#", "###"), "П": ("###", "#.#", "#.#", "#.#", "#.#"),
    "Р": ("##.", "#.#", "##.", "#..", "#.."), "С": (".##", "#..", "#..", "#..", ".##"),
    "Т": ("###", ".#.", ".#.", ".#.", ".#."), "У": ("#.#", "#.#", ".##", "..#", "##."),
    "Ф": (".#.", "###", "#.#", "###", ".#."), "Х": ("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Ч": ("#.#", "#.#", ".##", "..#", "..#"), "Ш": ("#.#", "#.#", "#.#", "#.#", "###"),
    "Я": (".##", "#.#", ".##", "#.#", "#.#"),
}
for _ch, _rows in CYRILLIC.items():
    cc0.TINY[ord(_ch)] = np.array([[c == "#" for c in r] for r in _rows])


def ring(cx, cy, r, n=20):
    return [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def tryzub_mask():
    """12x18 trident: centre spike, two curved side prongs, a base bar and foot."""
    g = cc0.Glyph()
    g.poly([(6, 0.5), (7.6, 4), (6.9, 4), (6.9, 17.5), (5.1, 17.5), (5.1, 4), (4.4, 4)])  # centre
    for s in (0, 1):
        x = lambda v: v if s == 0 else 12 - v
        g.poly([(x(0.5), 2), (x(2.2), 4), (x(2.2), 12), (x(0.5), 12)])  # side prong
        g.poly([(x(1.0), 12), (x(5.1), 15), (x(5.1), 13.4), (x(2.2), 11)])  # curve into the stem
    g.poly([(6, 6), (7.2, 7.4), (6, 8.8), (4.8, 7.4)])
    return g.fg


def tryzub():
    g = cc0.Glyph()
    g.fg |= tryzub_mask()
    return g.finish()


def flag():
    g = cc0.Glyph()
    g.rect(1, 2, 1, 16)
    g.rect(3, 3, 11, 8, fill=False)  # blue band: outline
    g.rect(3, 9, 11, 14)  # yellow band: solid
    return g.finish()


def heart_home():
    g = cc0.Glyph()
    pts = []
    for t in np.linspace(0, 2 * math.pi, 40, endpoint=False):
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((6 + x * 0.34, 8.5 - y * 0.34))
    g.poly(pts)
    return g.finish()


def sunflower(petals):
    """Battery gauge: a sunflower that loses petals as the charge drops. `petals` is 0-8."""
    g = cc0.Glyph()
    cx, cy = 6, 6.5
    for i in range(petals):
        a = 2 * math.pi * i / 8 - math.pi / 2
        g.poly(ring(cx + 3.9 * math.cos(a), cy + 3.9 * math.sin(a), 1.55, 12))
    g.poly(ring(cx, cy, 2.6, 16))
    g.rect(5, 12, 6, 17)  # stem
    g.px(4, 14), g.px(3, 13)  # leaf
    g.px(7, 15), g.px(8, 14)
    disc = np.zeros((CH, CW), bool)
    for y in range(CH):
        for x in range(CW):
            disc[y, x] = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= 1.5 ** 2
    g.fg &= ~disc  # dark seed centre
    return g.finish()


def wheat():
    g = cc0.Glyph()
    g.rect(5, 6, 6, 17)
    g.rect(5, 1, 6, 3)
    for y in (4, 7, 10):
        for dx in (-1, 1):
            g.rect(5 + (-2 if dx < 0 else 3), y, 5 + (-2 if dx < 0 else 3) + 1, y + 1)
            g.px(5 + (-1 if dx < 0 else 2), y + 2)
    return g.finish()


def drone():
    g = cc0.Glyph()
    g.rect(4, 7, 7, 10)
    for (x0, y0, x1, y1) in ((3, 5, 4, 7), (8, 5, 7, 7), (3, 12, 4, 10), (8, 12, 7, 10)):
        g.line(x0, y0, x1, y1)
    for x, y in ((0, 3), (9, 3), (0, 13), (9, 13)):
        g.rect(x, y, x + 2, y + 1)
    return g.finish()


def stork():
    """A standing stork in profile: long beak, curved neck, folded wing, long legs."""
    g = cc0.Glyph()
    g.rect(6, 1, 8, 2)  # head
    g.rect(1, 2, 5, 2)  # beak
    g.rect(7, 3, 8, 7)  # neck
    g.poly([(3, 8), (9, 6.5), (11, 9), (8, 12), (4, 11)])  # body
    g.line(6, 12, 6, 17)
    g.line(8, 12, 8, 17)
    g.rect(5, 17, 6, 17)
    g.rect(7, 17, 9, 17)
    return g.finish()


def logo():
    """288x72 boot logo: tryzub, UKRAINE in Public Pixel, and 'Slava Ukraini' in tiny Cyrillic."""
    W, H = 288, 72
    fg = np.zeros((H, W), bool)
    big = np.kron(tryzub_mask(), np.ones((3, 3), bool))
    fg[9:9 + big.shape[0], 24:24 + big.shape[1]] |= big

    def stamp(text, glyphs, scale, x, y, adv):
        for ch in text:
            g = glyphs.get(ord(ch))
            if g is not None:
                b = np.kron(g, np.ones((scale, scale), bool))
                fg[y:y + b.shape[0], x:x + b.shape[1]] |= b
            x += adv * scale

    stamp("UKRAINE", cc0.PUBLIC_PIXEL, 3, 72, 12, 9)
    fg[40:42, 72:264] = True
    stamp("СЛАВА УКРАЇНІ", cc0.TINY, 2, 72, 46, 4)
    p = np.pad(fg, 1)
    grown = np.zeros_like(fg)
    for dy in range(3):
        for dx in range(3):
            grown |= p[dy:dy + H, dx:dx + W]
    img = np.full((H, W), TRANSPARENT, np.uint8)
    img[grown] = BLACK
    img[fg] = WHITE
    return [img[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW] for r in range(4) for c in range(24)]


def build():
    chars = cc0.build()
    u = cc0.units
    S = {
        0x05: heart_home(), 0x11: tryzub(), 0x24: flag(), 0x70: drone(), 0x71: stork(), 0x97: wheat(),
        0x06: u("В", y=7), 0x07: u("МА", "Г"), 0x0C: u("М", y=7), 0x0F: u("ФТ", y=7), 0x12: u("ОБ", y=7),
        0x14: u("КРН", y=7), 0x15: u("ТАН", y=7), 0x7B: u("ЯЗ", y=7), 0x7D: u("КМ", y=7), 0x7E: u("МІЛ", y=7),
        0x7F: u("АЛТ", y=7), 0x89: u("ШРТ", y=7), 0x98: u("ДОВ", y=7), 0x99: u("ФТ", "С"), 0x9A: u("А", y=7),
        0x9B: u("УВ", "Х"), 0x9C: u("ПОЛ", "Х"), 0x9D: u("МІ", "Г"), 0x9E: u("КМ", "Г"), 0x9F: u("М", "С"),
    }
    for i, n in enumerate([8, 7, 6, 4, 3, 1, 0]):  # 0x90 full ... 0x96 empty
        S[0x90 + i] = sunflower(n)
    for code, c in S.items():
        chars[code] = c
    for i, t in enumerate(logo()):
        chars[0xA0 + i] = t
    return chars


if __name__ == "__main__":
    chars = build()
    with open(os.path.join(HERE, "ukraine.mcm"), "w", newline="") as f:
        f.write(mcm_text(chars))
    cc0.preview(chars, os.path.join(HERE, "ukraine-preview.png"))
    print("wrote iconsets/ukraine.mcm and iconsets/ukraine-preview.png")
