from pathlib import Path
import argparse
import pyxel


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "source" / "image2"
PYXRES = ROOT / "assets.pyxres"
SRC_SIZE = 1254
SURFACE_SRC_SIZE = 128

MONSTERS = [
    ("monster_slime.png", 0, 0),
    ("monster_bat.png", 32, 0),
    ("monster_skeleton.png", 64, 0),
    ("monster_goblin.png", 96, 0),
    ("monster_orc_chief.png", 128, 0),
    ("monster_revenant.png", 160, 0),
    ("monster_wraith.png", 192, 0),
    ("monster_golem.png", 224, 0),
    ("monster_mimic.png", 0, 32),
    ("monster_wyvern.png", 32, 32),
    ("monster_dungeon_master.png", 64, 32),
    ("monster_archdemon.png", 96, 32),
    ("monster_kobold.png", 128, 32),
    ("monster_ooze.png", 160, 32),
    ("monster_cultist.png", 192, 32),
    ("monster_ice_hound.png", 224, 32),
    ("monster_dark_knight.png", 0, 96),
    ("monster_lich.png", 32, 96),
]

WALLS = [
    ("wall_b1_b2.png", 0, 64, None),
    ("wall_b3_b4.png", 8, 64, {3: 11, 5: 13}),
    ("wall_b5_plus.png", 16, 64, {3: 2, 4: 8, 5: 1, 6: 13}),
]

BACKGROUNDS = [
    ("background_title.png", 1),
    ("background_ending.png", 2),
]

SURFACE_TILE_SIZE = 16

SURFACES = [
    ("surface_b1_b2_ceiling.png", 0, 128, None),
    ("surface_b1_b2_side_wall.png", 16, 128, None),
    ("surface_b1_b2_front_wall.png", 32, 128, None),
    ("surface_b1_b2_floor.png", 48, 128, None),
    ("surface_b1_b2_far.png", 64, 128, None),
    ("surface_b3_b4_ceiling.png", 80, 128, None),
    ("surface_b3_b4_side_wall.png", 96, 128, None),
    ("surface_b3_b4_front_wall.png", 112, 128, None),
    ("surface_b3_b4_floor.png", 128, 128, None),
    ("surface_b3_b4_far.png", 144, 128, None),
    ("surface_b5_plus_ceiling.png", 160, 128, None),
    ("surface_b5_plus_side_wall.png", 176, 128, None),
    ("surface_b5_plus_front_wall.png", 192, 128, None),
    ("surface_b5_plus_floor.png", 208, 128, None),
    ("surface_b5_plus_far.png", 224, 128, None),
]


def _solid_tile(col: int) -> list[list[int]]:
    return [[col for _ in range(SURFACE_TILE_SIZE)] for _ in range(SURFACE_TILE_SIZE)]


def _surface_h_scuffs(base: int, accent: int) -> list[list[int]]:
    tile = _solid_tile(base)
    for y, x0, x1 in (
        (1, 2, 5), (1, 10, 12),
        (4, 0, 3), (4, 7, 9), (4, 13, 15),
        (8, 4, 7), (8, 11, 14),
        (12, 1, 4), (12, 8, 10),
        (14, 5, 6), (14, 12, 15),
    ):
        for x in range(x0, x1 + 1):
            tile[y][x] = accent
    return tile


def _surface_v_scuffs(base: int, accent: int) -> list[list[int]]:
    tile = _solid_tile(base)
    for x, y0, y1 in (
        (1, 2, 5), (1, 10, 12),
        (4, 0, 3), (4, 7, 9), (4, 13, 15),
        (8, 4, 7), (8, 11, 14),
        (12, 1, 4), (12, 8, 10),
        (14, 5, 6), (14, 12, 15),
    ):
        for y in range(y0, y1 + 1):
            tile[y][x] = accent
    return tile


def _surface_far(dark: int, mid: int) -> list[list[int]]:
    tile = _solid_tile(dark)
    for x, y in ((4, 3), (11, 3), (7, 7), (13, 9), (2, 12), (9, 13)):
        tile[y][x] = mid
    return tile


SURFACE_PATTERNS = {
    "surface_b1_b2_ceiling.png": _surface_h_scuffs(13, 7),
    "surface_b1_b2_side_wall.png": _surface_v_scuffs(13, 7),
    "surface_b1_b2_front_wall.png": _surface_v_scuffs(13, 7),
    "surface_b1_b2_floor.png": _surface_h_scuffs(13, 7),
    "surface_b1_b2_far.png": _surface_far(0, 13),
    "surface_b3_b4_ceiling.png": _surface_h_scuffs(5, 3),
    "surface_b3_b4_side_wall.png": _surface_v_scuffs(5, 3),
    "surface_b3_b4_front_wall.png": _surface_v_scuffs(5, 3),
    "surface_b3_b4_floor.png": _surface_h_scuffs(5, 3),
    "surface_b3_b4_far.png": _surface_far(0, 5),
    "surface_b5_plus_ceiling.png": _surface_h_scuffs(1, 2),
    "surface_b5_plus_side_wall.png": _surface_v_scuffs(1, 2),
    "surface_b5_plus_front_wall.png": _surface_v_scuffs(1, 2),
    "surface_b5_plus_floor.png": _surface_h_scuffs(1, 2),
    "surface_b5_plus_far.png": _surface_far(0, 1),
}


def _load_png(path: Path, size: int = SRC_SIZE) -> pyxel.Image:
    img = pyxel.Image(size, size)
    img.load(0, 0, str(path.resolve()))
    return img


def _clear_rect(dst: pyxel.Image, x: int, y: int, w: int, h: int) -> None:
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            dst.pset(xx, yy, 0)


def _monster_bbox(src: pyxel.Image, bg_col: int = 3) -> tuple[int, int, int, int]:
    min_x = SRC_SIZE
    min_y = SRC_SIZE
    max_x = -1
    max_y = -1
    step = 2
    for y in range(0, SRC_SIZE, step):
        for x in range(0, SRC_SIZE, step):
            if src.pget(x, y) != bg_col:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < 0:
        return (0, 0, SRC_SIZE - 1, SRC_SIZE - 1)
    pad = 24
    return (
        max(0, min_x - pad),
        max(0, min_y - pad),
        min(SRC_SIZE - 1, max_x + pad),
        min(SRC_SIZE - 1, max_y + pad),
    )


def _square_box(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    w = x1 - x0 + 1
    h = y1 - y0 + 1
    size = max(w, h)
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    nx0 = max(0, min(SRC_SIZE - size, cx - size // 2))
    ny0 = max(0, min(SRC_SIZE - size, cy - size // 2))
    return (nx0, ny0, nx0 + size - 1, ny0 + size - 1)


def _blit_scaled(
    src: pyxel.Image,
    dst: pyxel.Image,
    src_box: tuple[int, int, int, int],
    dst_x: int,
    dst_y: int,
    dst_w: int,
    dst_h: int,
    transparent: int | None = None,
    remap: dict[int, int] | None = None,
) -> None:
    sx0, sy0, sx1, sy1 = src_box
    sw = max(1, sx1 - sx0 + 1)
    sh = max(1, sy1 - sy0 + 1)
    for y in range(dst_h):
        sy = sy0 + y * sh // dst_h
        for x in range(dst_w):
            sx = sx0 + x * sw // dst_w
            col = src.pget(sx, sy)
            if transparent is not None and col == transparent:
                col = 0
            if remap and col in remap:
                col = remap[col]
            dst.pset(dst_x + x, dst_y + y, col)


def _blit_surface_pattern(dst: pyxel.Image, pattern: list[list[int]], x: int, y: int) -> None:
    for yy, row in enumerate(pattern):
        for xx, col in enumerate(row):
            dst.pset(x + xx, y + yy, col)


def import_monsters() -> None:
    dst = pyxel.images[0]
    for filename, u, v in MONSTERS:
        path = SOURCE / "monsters" / filename
        if not path.exists():
            print(f"[WARN] missing monster source: {path}")
            continue
        src = _load_png(path)
        bg = src.pget(0, 0)
        box = _square_box(_monster_bbox(src, bg))
        _clear_rect(dst, u, v, 32, 32)
        _blit_scaled(src, dst, box, u, v, 32, 32, transparent=bg)
        print(f"[OK] monster {filename} -> ({u},{v}) bg={bg} box={box}")


def import_walls() -> None:
    dst = pyxel.images[0]
    for filename, u, v, remap in WALLS:
        path = SOURCE / "walls" / filename
        if not path.exists():
            fallback = SOURCE / "walls" / "wall_source.png"
            path = fallback if fallback.exists() else path
        if not path.exists():
            print(f"[WARN] missing wall source: {filename}")
            continue
        src = _load_png(path, SURFACE_SRC_SIZE)
        _blit_scaled(src, dst, (0, 0, SURFACE_SRC_SIZE - 1, SURFACE_SRC_SIZE - 1),
                     u, v, SURFACE_TILE_SIZE, SURFACE_TILE_SIZE, remap=remap)
        print(f"[OK] wall {path.name} -> ({u},{v})")


def import_backgrounds() -> None:
    for filename, bank in BACKGROUNDS:
        path = SOURCE / "backgrounds" / filename
        if not path.exists():
            fallback = SOURCE / "backgrounds" / "background_source.png"
            path = fallback if fallback.exists() else path
        if not path.exists():
            print(f"[WARN] missing background source: {filename}")
            continue
        src = _load_png(path)
        dst = pyxel.images[bank]
        _blit_scaled(src, dst, (0, 0, SRC_SIZE - 1, SRC_SIZE - 1),
                     0, 0, 256, 256)
        print(f"[OK] background {path.name} -> bank {bank}")


def import_surfaces() -> None:
    dst = pyxel.images[0]
    for filename, u, v, remap in SURFACES:
        pattern = SURFACE_PATTERNS.get(filename)
        if pattern is not None:
            _blit_surface_pattern(dst, pattern, u, v)
            print(f"[OK] surface pattern {filename} -> ({u},{v})")
            continue
        path = SOURCE / "surfaces" / filename
        if not path.exists():
            print(f"[WARN] missing surface source: {filename}")
            continue
        src = _load_png(path)
        _blit_scaled(src, dst, (0, 0, SRC_SIZE - 1, SRC_SIZE - 1),
                     u, v, 8, 8, remap=remap)
        print(f"[OK] surface {path.name} -> ({u},{v})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monsters", action="store_true")
    parser.add_argument("--walls", action="store_true")
    parser.add_argument("--backgrounds", action="store_true")
    parser.add_argument("--surfaces", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    pyxel.init(16, 16, display_scale=1)
    if PYXRES.exists():
        pyxel.load(str(PYXRES))

    do_all = args.all or not (
        args.monsters or args.walls or args.backgrounds or args.surfaces
    )
    if do_all or args.monsters:
        import_monsters()
    if do_all or args.walls:
        import_walls()
    if do_all or args.backgrounds:
        import_backgrounds()
    if do_all or args.surfaces:
        import_surfaces()

    pyxel.save(str(PYXRES))
    print(f"[OK] saved {PYXRES}")


if __name__ == "__main__":
    main()
