"""Build the website data from fonts/catalog.toml and iconsets/.

    uv run build.py            # site/data/*.json, site/f/<id>.html + .png, site/sitemap.xml

site/data/fonts.json      catalog + raw 1-bit text glyphs (the browser places them in cells)
site/data/iconsets.json   icon sets (256 packed glyphs each) + symbol groups
site/f/<id>.html          one crawlable page per font, with a PNG preview
site/f/<id>-card.png      1200x630 social share card per font
site/og/*.png             social share cards for the top-level pages
"""
import html
import json
import os
import sys
import tomllib

import numpy as np
from PIL import Image

from osdfont.glyphs import (build_font, fingerprint, fits, is_native, legibility, load_source,
                            reference_shapes, size_of)
from osdfont import card
from osdfont.traits import describe
from osdfont.mcm import BLACK, CH, CW, GLYPHS, TRANSPARENT, WHITE, pack, read_mcm

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
BASE_URL = "https://over9kfpv.github.io/osd-fonts/"
COLLECTIONS = {
    "pc": "IBM PC ROM fonts",
    "vault": "Terminal & game fonts",
    "cc0": "CC0 collection (OpenGameArt)",
    "demoscene": "Demoscene (unknown authors)",
}


def parse_codes(specs):
    codes = []
    for s in specs:
        a, _, b = s.partition("-")
        codes += range(int(a, 16), int(b or a, 16) + 1)
    return codes


def load_groups():
    groups = tomllib.load(open(os.path.join(ROOT, "iconsets", "groups.toml"), "rb"))["group"]
    taken = set()
    for g in groups:
        g["codes"] = parse_codes(g["codes"])
        if taken & set(g["codes"]):
            raise ValueError(f"group {g['id']} overlaps another group: {sorted(taken & set(g['codes']))}")
        taken |= set(g["codes"])
    rest = [g for g in groups if g["id"] == "other"][0]
    rest["codes"] = [c for c in range(GLYPHS) if c not in taken]
    return groups


def load_iconsets():
    meta = tomllib.load(open(os.path.join(ROOT, "iconsets", "iconsets.toml"), "rb"))["iconset"]
    for s in meta:
        s["chars"] = read_mcm(os.path.join(ROOT, "iconsets", s["file"]))
    return meta


def load_catalog():
    return tomllib.load(open(os.path.join(ROOT, "fonts", "catalog.toml"), "rb"))["font"]


def load_fonts(catalog, reference):
    """Load every font, enforcing the catalog rules: unique ids, fits 12x18, no duplicate letters."""
    fonts, ids, prints = [], set(), {}
    for e in catalog:
        if e["id"] in ids:
            raise ValueError(f"duplicate id {e['id']}")
        ids.add(e["id"])
        glyphs = load_source(e, os.path.join(ROOT, "fonts"), reference)
        if not fits(glyphs):
            raise ValueError(f"{e['id']}: {size_of(glyphs)} does not fit a 12x18 cell with outline")
        fp = fingerprint(glyphs)
        if fp in prints:
            raise ValueError(f"{e['id']}: same letters as {prints[fp]}")
        prints[fp] = e["id"]
        fonts.append((e, glyphs, legibility(glyphs, reference)))
    return fonts


PREVIEW_TEXT = ("ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "0123456789.:-")
PALETTE = {BLACK: (0, 0, 0), WHITE: (255, 255, 255), TRANSPARENT: (58, 72, 86)}


def preview_png(chars, path, scale=2):
    cols = max(len(t) for t in PREVIEW_TEXT)
    img = np.zeros((len(PREVIEW_TEXT) * CH, cols * CW, 3), np.uint8)
    img[:] = PALETTE[TRANSPARENT]
    for r, line in enumerate(PREVIEW_TEXT):
        for i, ch in enumerate(line):
            cell = chars[ord(ch)]
            for v, rgb in PALETTE.items():
                img[r * CH:(r + 1) * CH, i * CW:(i + 1) * CW][cell == v] = rgb
    Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(path, optimize=True)


FONT_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{name} · OSD Fonts</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{name} · Betaflight OSD font">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="OSD Fonts">
<meta property="og:url" content="{base}f/{id}.html">
<meta property="og:image" content="{base}f/{id}-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{name} letters on a Betaflight OSD font grid">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{base}f/{id}.html">
<link rel="icon" href="../assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="../assets/style.css">
<script>try {{ const t = localStorage.getItem("osdf-theme"); if (t) document.documentElement.dataset.theme = t }} catch (e) {{}}</script>
</head>
<body>
<div class="wrap">
  <header class="top">
    <a class="logo" href="../index.html"><svg viewBox="0 0 32 32" aria-hidden="true"><rect x="2" y="5" width="28" height="22" rx="6" fill="currentColor"/><path fill="var(--ground)" d="M13 10h6v2h-6zM11 12h2v10h-2zM19 12h2v10h-2zM13 16h6v2h-6z"/><circle cx="25.5" cy="9.5" r="1.7" fill="var(--accent)"/></svg>OSD Fonts</a>
    <nav class="nav" aria-label="Main"><a href="../index.html#fonts">Retro fonts</a><a href="../mix.html">Mix fonts &amp; icons</a><a href="../editor.html">Font editor</a><a href="../install.html">Install</a><a href="https://github.com/Over9kfpv/osd-fonts">GitHub</a></nav>
  </header>
  <main class="font-page">
    <div>
      <p class="eyebrow">{collection}</p>
      <h1>{name}</h1>
      <p class="lede">{desc}</p>
      <div class="ctas"><a class="btn accent" href="../index.html#{id}">Try it on the OSD</a><a class="btn ghost" href="../mix.html?font={id}">Mix with icons →</a><a class="btn ghost" href="../editor.html?font={id}">Edit</a></div>{pd}
    </div>
    <div class="bundle">
      <img class="font-preview" src="{id}.png" width="{pw}" height="{ph}" alt="{name}: A to Z and 0 to 9 as they appear on the OSD">
      <dl class="meta">{meta}</dl>
    </div>
  </main>
  <footer class="site">
    <p>Free downloads · Open source. Each font keeps its own license; icons come from Betaflight Configurator (GPL-3.0).</p>
    <p><a href="../install.html">How to install</a> · <a href="https://github.com/Over9kfpv/osd-fonts">Source on GitHub</a> · <a href="https://over9kfpv.github.io/stickbeats/">Stickbeats</a></p>
  </footer>
</div>
<script type="module" src="../assets/theme.js"></script>
</body>
</html>
"""


def font_page(e, glyphs, native, png_size):
    w, h = size_of(glyphs)
    how = "used at native size" if native else "centred 1:1, or doubled in height if you pick Tall"
    desc = (f"{e['name']} as a Betaflight analog OSD font: {w}×{h} px letters, {how}, "
            f"with a black outline and the stock Betaflight symbols.")
    rows = [("Collection", COLLECTIONS[e["collection"]]), ("Letter size", f"{w}×{h} px"),
            ("License", e["license"]), ("Author", e.get("author") or "Unknown"),
            ("Source", f'<a href="{html.escape(e["url"])}">{html.escape(e["url"])}</a>' if e.get("url") else "—")]
    meta = "".join(f"<dt>{k}</dt><dd>{v if k == 'Source' else html.escape(v)}</dd>" for k, v in rows)
    pd = ""
    if e["license"].startswith(("CC0", "Public domain")):
        pd = (f'\n      <p class="lede" style="margin-top:18px">These letters are public domain. Pair them with the '
              f'<a href="../mix.html?font={e["id"]}&amp;icons=cc0">OSD Fonts CC0 icon set</a> and the whole font is public domain too.</p>')
    return FONT_PAGE.format(name=html.escape(e["name"]), desc=html.escape(desc), id=e["id"], base=BASE_URL, pd=pd,
                            collection=COLLECTIONS[e["collection"]], meta=meta, pw=png_size[0], ph=png_size[1])


CARD_GRID = dict(x=660, y=27, cols=14, scale=3)
CARD_FIRST = 20  # 140 cells: 20..159, symbols around the letters, stopping before the logo


def title_runs(text, chars, glyphs):
    """Wrap a title into lines of one font's OSD letters."""
    text = "".join(ch if 0x20 <= ord(ch) <= 0x5F else " " for ch in text.upper())
    lines = [text] if len(text) <= 12 else card.wrap(text, max(12, (len(text) + 2) // 2))
    return [[(line, chars, size_of(glyphs)[0])] for line in lines[:3]]


def font_card(e, glyphs, chars, label, path):
    w, h = size_of(glyphs)
    codes = list(range(CARD_FIRST, CARD_FIRST + 140))
    first = next((ord(ch) for ch in e["name"].upper() if ord(ch) in codes and ord(ch) > 0x40), 0x41)
    lic = "license unknown" if e["license"].lower() == "unknown" else e["license"]
    sub = f"Betaflight OSD font. {w}x{h} px letters, {lic}"
    card.draw(path, title_runs(e["name"], chars, glyphs), sub, label,
              dict(CARD_GRID, cells=[chars[c] for c in codes], numbers=codes, selected=codes.index(first)))


def page_cards(fonts, built, iconsets, label):
    """Cards for index, mix, editor and install, in site/og/."""
    out = os.path.join(SITE, "og")
    os.makedirs(out, exist_ok=True)
    by_id = {e["id"]: (e, g, c) for (e, g, _), c in zip(fonts, built)}
    # Titles use the featured fonts that read most like the stock Betaflight letters.
    featured = [by_id[e["id"]] for e, _, score in sorted(fonts, key=lambda f: -f[2]) if e.get("featured")][:8] \
        or list(by_id.values())
    pick = lambda i: featured[i % len(featured)]
    run = lambda text, i: (text, pick(i)[2], size_of(pick(i)[1])[0])
    grid = dict(CARD_GRID)

    # Home: every cell a letter from a different font.
    letters = [ord(ch) for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"]
    cells = [built[i * 7 % len(built)][letters[i % len(letters)]] for i in range(140)]
    card.draw(os.path.join(out, "home.png"),
              [[run("GIVE YOUR", 0)], [run("OSD A", 1)], [run("RETRO FONT.", 2)]],
              f"{len(fonts)} free retro fonts for the Betaflight analog OSD", label,
              dict(grid, cells=cells, numbers=[letters[i % len(letters)] for i in range(140)], selected=62))

    vga = by_id.get("ibm-vga-8x16", featured[0])
    sets = {s["id"]: s["chars"] for s in iconsets}
    # Mix: one font's letters over the public-domain icon set.
    mixed = build_font(vga[1], sets.get("cc0", sets["default"]), "small")
    codes = list(range(CARD_FIRST, CARD_FIRST + 140))
    card.draw(os.path.join(out, "mix.png"), [[run("MIX FONTS", 0)], [run("& ICONS", 1)]],
              "Any text font, any Betaflight icon set, one .mcm file", label,
              dict(grid, cells=[mixed[c] for c in codes], numbers=codes, selected=codes.index(0x41)))

    # Editor: the character map as the editor shows it. 24 columns from 16, so the boot logo
    # (160-255, 24 characters wide) assembles the way Betaflight lays it out.
    codes = list(range(16, 256))
    vrun = lambda text: (text, vga[2], size_of(vga[1])[0])
    card.draw(os.path.join(out, "editor.png"), [[vrun("MAX7456")], [vrun("FONT")], [vrun("EDITOR")]],
              "Draw and upload OSD fonts in the browser", label,
              dict(x=552, y=(card.H - 10 * 39) // 2, cols=24, scale=2, gap=3, cells=[vga[2][c] for c in codes], numbers=None, selected=codes.index(0x41)))

    # Install: the letters, ready to go.
    codes = list(range(CARD_FIRST, CARD_FIRST + 140))
    card.draw(os.path.join(out, "install.png"), [[run("INSTALL", 3)], [run("A FONT", 4)]],
              "With Betaflight Configurator or straight from the browser over USB", label,
              dict(grid, cells=[pick(5)[2][c] for c in codes], numbers=codes, selected=codes.index(0x41)))


def main():
    iconsets = load_iconsets()
    stock = [s for s in iconsets if s["id"] == "default"][0]["chars"]
    reference = reference_shapes(stock)
    groups = load_groups()
    fonts = load_fonts(load_catalog(), reference)

    os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
    os.makedirs(os.path.join(SITE, "f"), exist_ok=True)
    out_fonts, built = [], []
    traits = describe(fonts)
    label = [g for e, g, _ in fonts if e["id"] == "ibm-vga-8x16"][0]
    for (e, glyphs, score), t in zip(fonts, traits):
        native = is_native(glyphs)
        w, h = size_of(glyphs)
        chars = build_font(glyphs, stock, "small")
        png = os.path.join(SITE, "f", f"{e['id']}.png")
        preview_png(chars, png)
        font_card(e, glyphs, chars, label, os.path.join(SITE, "f", f"{e['id']}-card.png"))
        built.append(chars)
        with open(os.path.join(SITE, "f", f"{e['id']}.html"), "w") as f:
            f.write(font_page(e, glyphs, native, Image.open(png).size))
        out_fonts.append({
            "id": e["id"], "name": e["name"], "collection": e["collection"],
            "license": e["license"], "author": e.get("author"), "url": e.get("url"),
            "featured": e.get("featured", False), "size": f"{w}x{h}", "native": bool(native),
            "score": round(float(score), 3),
            **t,
            "glyphs": {str(c): ["".join("1" if p else "0" for p in row) for row in g] for c, g in glyphs.items()},
        })
    with open(os.path.join(SITE, "data", "fonts.json"), "w") as f:
        json.dump({"collections": COLLECTIONS, "fonts": out_fonts}, f, separators=(",", ":"))
    with open(os.path.join(SITE, "data", "iconsets.json"), "w") as f:
        json.dump({
            "groups": [{k: g[k] for k in ("id", "name", "about", "codes")} for g in groups],
            "iconsets": [{"id": s["id"], "name": s["name"], "license": s["license"], "glyphs": pack(s["chars"])}
                         for s in iconsets],
        }, f, separators=(",", ":"))
    page_cards(fonts, built, iconsets, label)
    pages = ["", "mix.html", "editor.html", "install.html"] + [f"f/{e['id']}.html" for e, _, _ in fonts]
    with open(os.path.join(SITE, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.writelines(f"  <url><loc>{BASE_URL}{p}</loc></url>\n" for p in pages)
        f.write("</urlset>\n")
    print(f"{len(fonts)} fonts, {len(iconsets)} icon sets, {len(groups)} groups -> site/", file=sys.stderr)


if __name__ == "__main__":
    main()
