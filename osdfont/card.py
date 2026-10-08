"""1200x630 social share cards, drawn like the font editor: a dark panel, a grid of numbered
glyph cells on a transparency checkerboard, and a title set in OSD letters."""
import numpy as np
from PIL import Image

from .mcm import BLACK, CH, CW, TRANSPARENT, WHITE

W, H = 1200, 630
BG = (35, 37, 41)
CELL_BG = (47, 50, 55)
CHECK = ((58, 61, 66), (46, 49, 54))
INK = (233, 232, 227)
DIM = (158, 162, 169)
ACCENT = (255, 86, 70)
SELECT = (93, 214, 232)

# 3x5 digits for the cell numbers, as in the editor.
DIGITS = ["111101101101111", "010110010010111", "111001111100111", "111001111001111", "101101111001001",
          "111100111001111", "111100111101111", "111001001010010", "111101111101111", "111101111001111"]


class Card:
    def __init__(self):
        self.img = np.zeros((H, W, 3), np.uint8)
        self.img[:] = BG

    def rect(self, x, y, w, h, rgb):
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
        if x1 > x0 and y1 > y0:
            self.img[y0:y1, x0:x1] = rgb

    def bits(self, x, y, mask, scale, rgb):
        m = np.repeat(np.repeat(mask, scale, 0), scale, 1)
        h, w = m.shape
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
        if x1 > x0 and y1 > y0:
            self.img[y0:y1, x0:x1][m[y0 - y:y1 - y, x0 - x:x1 - x]] = rgb

    def number(self, x, y, n, rgb):
        for i, d in enumerate(f"{n:03d}"):
            self.bits(x + i * 8, y, np.array(list(DIGITS[int(d)]), int).reshape(5, 3) == 1, 2, rgb)

    def label(self, x, y, text, glyphs, scale, rgb):
        """Plain one-colour text from raw glyphs (no outline); returns the width drawn."""
        adv = max(g.shape[1] for g in glyphs.values()) + 1
        for i, ch in enumerate(text.upper()):
            if ord(ch) in glyphs:
                self.bits(x + i * adv * scale, y, glyphs[ord(ch)], scale, rgb)
        return len(text) * adv * scale

    def cell(self, x, y, cell, scale, number=None, selected=False):
        """One editor cell: checkerboard where the glyph is transparent, black and white on top."""
        w, h = CW * scale, CH * scale
        yy, xx = np.mgrid[0:h, 0:w] // (2 * scale)
        tile = np.where(((yy + xx) % 2 == 0)[..., None], CHECK[0], CHECK[1]).astype(np.uint8)
        big = np.repeat(np.repeat(cell, scale, 0), scale, 1)
        tile[big == BLACK] = (0, 0, 0)
        tile[big == WHITE] = (255, 255, 255)
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
        if x1 > x0 and y1 > y0:
            self.img[y0:y1, x0:x1] = tile[y0 - y:y1 - y, x0 - x:x1 - x]
        if number is not None:
            self.number(x + 3, y + 3, number, DIM)
        if selected:
            for t in range(3):
                self.rect(x - 3 - t, y - 3 - t, w + 6 + 2 * t, 1, SELECT)
                self.rect(x - 3 - t, y + h + 2 + t, w + 6 + 2 * t, 1, SELECT)
                self.rect(x - 3 - t, y - 3 - t, 1, h + 6 + 2 * t, SELECT)
                self.rect(x + w + 2 + t, y - 3 - t, 1, h + 6 + 2 * t, SELECT)

    def grid(self, x, y, cells, cols, scale, numbers=None, selected=None, gap=4):
        """cells: list of 12x18 arrays, laid out like the editor's character map."""
        pw, ph = CW * scale + gap, CH * scale + gap
        for i, c in enumerate(cells):
            r, k = divmod(i, cols)
            self.cell(x + k * pw, y + r * ph, c, scale,
                      None if numbers is None else numbers[i], selected == i)

    def title(self, x, y, lines, max_w, max_h):
        """OSD text at the largest scale that fits. lines: [[(text, chars, ink_w), ...], ...];
        each run keeps its own font's cells, cropped to the ink plus outline. Returns the height."""
        def width(line, s):
            return sum(len(t) * (w + 2) * s for t, _, w in line)
        scale = max([s for s in range(2, 9) if all(width(l, s) <= max_w for l in lines)
                     and len(lines) * CH * s <= max_h] or [2])
        for n, line in enumerate(lines):
            cx = x
            for text, chars, w in line:
                ox = (CW - w) // 2 - 1
                for ch in text:
                    cell = chars[ord(ch)][:, ox:ox + w + 2]
                    self.bits(cx, y + n * CH * scale, cell == BLACK, scale, (0, 0, 0))
                    self.bits(cx, y + n * CH * scale, cell == WHITE, scale, (255, 255, 255))
                    cx += (w + 2) * scale
        return len(lines) * CH * scale

    def save(self, path):
        Image.fromarray(self.img).quantize(64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) \
            .save(path, optimize=True)


def wrap(text, chars_per_line):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > chars_per_line:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur] if cur else lines


def draw(path, title_lines, sub, label_glyphs, grid, footer="OVER9KFPV.GITHUB.IO/OSD-FONTS"):
    """Left: eyebrow, title, subtitle (wrapped to the column), footer. Right: the glyph grid
    (dict of Card.grid args). The footer may run under a grid that ends above it."""
    c = Card()
    left, text_w = 64, grid["x"] - 64 - 40
    adv = (max(g.shape[1] for g in label_glyphs.values()) + 1) * 2
    sub = wrap(sub, text_w // adv)[:3]
    c.rect(left, 64, 16, 16, ACCENT)
    c.label(left + 28, 58, "OSD FONTS", label_glyphs, 2, ACCENT)
    th = c.title(left, 120, title_lines, text_w, 280)
    y = 120 + th + 32
    for line in sub:
        c.label(left, y, line, label_glyphs, 2, INK if y == 120 + th + 32 else DIM)
        y += 40
    c.label(left, H - 64 - 32, footer, label_glyphs, 2, DIM)
    c.grid(**grid)
    c.save(path)
