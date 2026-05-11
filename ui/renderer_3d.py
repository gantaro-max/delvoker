import pyxel
from constants import (
    FRAMES, MAX_DEPTH, WALL_COLS,
    COL_DARK_GRAY, COL_NAVY,
)

# Biome tile source coords (tx, ty) in image bank 0, each 8x8 px.
# floor 1-2 -> basic stone, 3-4 -> deeper stone, 5+ -> dark stone
_BIOME_TILES = [(0, 64), (8, 64), (16, 64)]


def _biome_tile(floor: int) -> tuple:
    if floor <= 2:
        return _BIOME_TILES[0]
    elif floor <= 4:
        return _BIOME_TILES[1]
    return _BIOME_TILES[2]


def _blt_tile(x: int, y: int, w: int, h: int, tx: int, ty: int) -> None:
    """Fill a rect by tiling an 8x8 sprite from image bank 0."""
    for row in range(y, y + h, 8):
        for col in range(x, x + w, 8):
            cw = min(8, x + w - col)
            ch = min(8, y + h - row)
            pyxel.blt(col, row, 0, tx, ty, cw, ch)


def _fill_wall(x: int, y: int, w: int, h: int, col: int,
               assets_loaded: bool, dungeon_floor: int) -> None:
    """Draw a wall face: textured when assets available, solid color otherwise."""
    if assets_loaded:
        tx, ty = _biome_tile(dungeon_floor)
        _blt_tile(x, y, w, h, tx, ty)
    else:
        pyxel.rect(x, y, w, h, col)


def draw_3d_view(wall_at_fn, assets_loaded: bool = False, dungeon_floor: int = 1):
    """Render the first-person 3D corridor view.

    wall_at_fn(fwd, side) -> bool: returns True if a wall exists at that
    relative position from the player (fwd=depth, side=-1/0/+1).
    assets_loaded: use pyxel.blt texture tiling when True, solid rect otherwise.
    dungeon_floor: current floor index for biome tile selection.
    """
    for d in range(MAX_DEPTH - 1, -1, -1):
        fx1, fy1, fx2, fy2 = FRAMES[d]
        nfx1, nfy1, nfx2, nfy2 = FRAMES[d + 1]
        wc = WALL_COLS[d] if d < len(WALL_COLS) else COL_DARK_GRAY
        pyxel.tri(fx1, fy1, fx2,  fy1, nfx2, nfy1, wc)
        pyxel.tri(fx1, fy1, nfx1, nfy1, nfx2, nfy1, wc)
        pyxel.tri(fx1, fy2, fx2,  fy2, nfx2, nfy2, wc)
        pyxel.tri(fx1, fy2, nfx1, nfy2, nfx2, nfy2, wc)

    nfx1, nfy1, nfx2, nfy2 = FRAMES[MAX_DEPTH]
    _fill_wall(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1,
               COL_NAVY, assets_loaded, dungeon_floor)

    visible = MAX_DEPTH
    for d in range(MAX_DEPTH):
        if wall_at_fn(d + 1, 0):
            visible = d + 1
            break

    for d in range(visible - 1, -1, -1):
        fx1, fy1, fx2, fy2 = FRAMES[d]
        nfx1, nfy1, nfx2, nfy2 = FRAMES[d + 1]
        front = wall_at_fn(d + 1, 0)
        left  = wall_at_fn(d,     -1)
        right = wall_at_fn(d,      1)
        wc = WALL_COLS[d] if d < len(WALL_COLS) else COL_DARK_GRAY
        if front:
            _fill_wall(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1,
                       wc, assets_loaded, dungeon_floor)
        if left:
            pyxel.tri(fx1, fy1, nfx1, nfy1, nfx1, nfy2, wc)
            pyxel.tri(fx1, fy1, fx1,  fy2,  nfx1, nfy2, wc)
        if right:
            pyxel.tri(nfx2, nfy1, fx2, fy1, fx2,  fy2,  wc)
            pyxel.tri(nfx2, nfy1, nfx2, nfy2, fx2, fy2, wc)
        if d < MAX_DEPTH - 1:
            if front:
                pyxel.rectb(nfx1, nfy1, nfx2 - nfx1 + 1,
                            nfy2 - nfy1 + 1, COL_DARK_GRAY)
            pyxel.line(fx1, fy1, nfx1, nfy1, COL_DARK_GRAY)
            pyxel.line(fx2, fy1, nfx2, nfy1, COL_DARK_GRAY)
            pyxel.line(fx1, fy2, nfx1, nfy2, COL_DARK_GRAY)
            pyxel.line(fx2, fy2, nfx2, nfy2, COL_DARK_GRAY)
