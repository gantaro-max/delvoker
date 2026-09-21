"""Render the four README screenshots without entering Pyxel's main loop."""

import os
import random
import struct
import sys
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs" / "screenshots"
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import pyxel  # noqa: E402


pyxel.run = lambda update, draw: None

import main  # noqa: E402
from constants import STATE_TITLE, STATE_TOWN  # noqa: E402


def write_scaled_png(path, scale=2):
    """Encode Pyxel's indexed framebuffer as a true-colour PNG."""
    width = pyxel.width * scale
    height = pyxel.height * scale
    rows = []
    for y in range(pyxel.height):
        row = bytearray(b"\x00")
        for x in range(pyxel.width):
            rgb = pyxel.colors[pyxel.screen.pget(x, y)]
            pixel = bytes(((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF))
            row.extend(pixel * scale)
        rows.extend([bytes(row)] * scale)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    payload = b"".join(rows)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(payload)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def settle_windows(app, frames=10):
    windows = (
        app.town_win, app.status_win, app.sub_win, app.battle_win,
        app.inv_win, app.inv_action_win, app.shop_win,
    )
    for _ in range(frames):
        for window in windows:
            window.update()


def capture(app, filename):
    settle_windows(app)
    app.draw()
    write_scaled_png(OUTPUT_DIR / filename)


def main_capture():
    random.seed(7)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    app = main.App()

    app._set_state(STATE_TITLE)
    capture(app, "01_title.png")

    app.player.gold = 250
    app._set_state(STATE_TOWN)
    capture(app, "02_town.png")

    app._enter_dungeon_fresh()
    capture(app, "03_dungeon.png")

    app._start_battle()
    capture(app, "04_battle.png")


if __name__ == "__main__":
    main_capture()
