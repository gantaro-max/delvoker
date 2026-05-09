import pyxel
from constants import (
    FRAMES, MAX_DEPTH, WALL_COLS,
    COL_DARK_GRAY, COL_NAVY,
)


def draw_3d_view(wall_at_fn):
    """Render the first-person 3D corridor view.

    wall_at_fn(fwd, side) -> bool: returns True if a wall exists at that
    relative position from the player (fwd=depth, side=-1/0/+1).
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
    pyxel.rect(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, COL_NAVY)

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
            pyxel.rect(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, wc)
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
