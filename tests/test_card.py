import numpy as np
from PIL import Image

from osdfont import card
from osdfont.mcm import CH, CW, TRANSPARENT


def test_card_is_1200x630(tmp_path):
    glyphs = {c: np.ones((8, 6), bool) for c in range(0x20, 0x60)}
    chars = [np.full((CH, CW), TRANSPARENT, np.uint8) for _ in range(256)]
    path = tmp_path / "card.png"
    card.draw(path, [[("A VERY LONG FONT NAME", chars, 6)]], "Betaflight OSD font. 6x8 px letters, CC0 1.0",
              glyphs, dict(x=660, y=27, cols=14, scale=3, cells=chars[:140], numbers=list(range(140)), selected=0))
    assert Image.open(path).size == (1200, 630)


def test_wrap_keeps_words():
    assert card.wrap("draw and upload osd fonts", 10) == ["draw and", "upload osd", "fonts"]
