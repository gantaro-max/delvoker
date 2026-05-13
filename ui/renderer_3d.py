import pyxel
from constants import (
    FRAMES, MAX_DEPTH, WALL_COLS, VIEW_H,
    COL_BLACK, COL_DARK_GRAY,
)

# Biome tile (tx, ty) in image bank 0; 8x8 sprite per biome tier.
# floor 1-2 -> basic stone, 3-4 -> deeper stone, 5+ -> dark stone
_BIOME_TILES = [(0, 64), (8, 64), (16, 64)]


def _biome_tile(floor: int) -> tuple:
    if floor <= 2:
        return _BIOME_TILES[0]
    if floor <= 4:
        return _BIOME_TILES[1]
    return _BIOME_TILES[2]


def _blt_tile_rect(x: int, y: int, w: int, h: int, tx: int, ty: int) -> None:
    """Tile an 8x8 sprite to fill a rect, aligned to the screen grid so
    neighbouring rects share seamless tile borders."""
    if w <= 0 or h <= 0:
        return
    x_end, y_end = x + w, y + h
    row = y
    while row < y_end:
        oy = row & 7
        ch = min(8 - oy, y_end - row)
        col = x
        while col < x_end:
            ox = col & 7
            cw = min(8 - ox, x_end - col)
            pyxel.blt(col, row, 0, tx + ox, ty + oy, cw, ch)
            col += cw
        row += ch


def _blt_tile_quad(tx: int, ty: int,
                   x1: int, x2: int,
                   yt1: int, yt2: int, yb1: int, yb2: int) -> None:
    """Tile-fill a quadrilateral by scanning 1px vertical strips from x1..x2.
    Top edge linearly interpolates yt1->yt2; bottom edge yb1->yb2.
    Used for side-wall trapezoids that taper into depth."""
    if x2 < x1:
        return
    dx = x2 - x1
    for x in range(x1, x2 + 1):
        t = (x - x1) / dx if dx > 0 else 0
        yt = int(yt1 + (yt2 - yt1) * t)
        yb = int(yb1 + (yb2 - yb1) * t)
        if yb < yt:
            continue
        ox = x & 7
        row = yt
        while row <= yb:
            oy = row & 7
            ch = min(8 - oy, yb - row + 1)
            pyxel.blt(x, row, 0, tx + ox, ty + oy, 1, ch)
            row += ch


def draw_3d_view(wall_at_fn, assets_loaded: bool = False, dungeon_floor: int = 1):
    """Render the first-person 3D corridor view."""
    tx, ty = _biome_tile(dungeon_floor)

    # --- Floor & Ceiling background -----------------------------------
    if assets_loaded:
        half = VIEW_H // 2
        _blt_tile_rect(0, 0,    256, half,          tx, ty)  # ceiling
        _blt_tile_rect(0, half, 256, VIEW_H - half, tx, ty)  # floor
    else:
        # Fallback: original solid-color perspective fan
        for d in range(MAX_DEPTH - 1, -1, -1):
            fx1, fy1, fx2, fy2 = FRAMES[d]
            nfx1, nfy1, nfx2, nfy2 = FRAMES[d + 1]
            wc = WALL_COLS[d] if d < len(WALL_COLS) else COL_DARK_GRAY
            pyxel.tri(fx1, fy1, fx2,  fy1, nfx2, nfy1, wc)
            pyxel.tri(fx1, fy1, nfx1, nfy1, nfx2, nfy1, wc)
            pyxel.tri(fx1, fy2, fx2,  fy2, nfx2, nfy2, wc)
            pyxel.tri(fx1, fy2, nfx1, nfy2, nfx2, nfy2, wc)

    # --- Far-end darkness (deeper than MAX_DEPTH) ---------------------
    nfx1, nfy1, nfx2, nfy2 = FRAMES[MAX_DEPTH]
    pyxel.rect(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, COL_BLACK)

    # --- Find nearest front wall --------------------------------------
    visible = MAX_DEPTH
    for d in range(MAX_DEPTH):
        if wall_at_fn(d + 1, 0):
            visible = d + 1
            break

    # --- Draw walls from far to near so near ones overdraw far ones ---
    for d in range(visible - 1, -1, -1):
        fx1, fy1, fx2, fy2 = FRAMES[d]
        nfx1, nfy1, nfx2, nfy2 = FRAMES[d + 1]
        front = wall_at_fn(d + 1, 0)
        left  = wall_at_fn(d,     -1)
        right = wall_at_fn(d,      1)
        wc = WALL_COLS[d] if d < len(WALL_COLS) else COL_DARK_GRAY

        if front:
            if assets_loaded:
                _blt_tile_rect(nfx1, nfy1,
                               nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, tx, ty)
            else:
                pyxel.rect(nfx1, nfy1,
                           nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, wc)

        if left:
            if assets_loaded:
                # Left side wall: trapezoid (fx1,fy1)-(nfx1,nfy1) top,
                # (fx1,fy2)-(nfx1,nfy2) bottom.
                _blt_tile_quad(tx, ty, fx1, nfx1, fy1, nfy1, fy2, nfy2)
            else:
                pyxel.tri(fx1, fy1, nfx1, nfy1, nfx1, nfy2, wc)
                pyxel.tri(fx1, fy1, fx1,  fy2,  nfx1, nfy2, wc)

        if right:
            if assets_loaded:
                # Right side wall: trapezoid (nfx2,nfy1)-(fx2,fy1) top,
                # (nfx2,nfy2)-(fx2,fy2) bottom.
                _blt_tile_quad(tx, ty, nfx2, fx2, nfy1, fy1, nfy2, fy2)
            else:
                pyxel.tri(nfx2, nfy1, fx2, fy1, fx2, fy2, wc)
                pyxel.tri(nfx2, nfy1, nfx2, nfy2, fx2, fy2, wc)

        # Depth outline (helps separate tiers visually)
        if d < MAX_DEPTH - 1:
            if front:
                pyxel.rectb(nfx1, nfy1, nfx2 - nfx1 + 1,
                            nfy2 - nfy1 + 1, COL_DARK_GRAY)
            pyxel.line(fx1, fy1, nfx1, nfy1, COL_DARK_GRAY)
            pyxel.line(fx2, fy1, nfx2, nfy1, COL_DARK_GRAY)
            pyxel.line(fx1, fy2, nfx1, nfy2, COL_DARK_GRAY)
            pyxel.line(fx2, fy2, nfx2, nfy2, COL_DARK_GRAY)
