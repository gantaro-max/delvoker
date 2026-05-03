import pyxel

SCREEN_W = 256
SCREEN_H = 256
FPS = 30
TITLE = "Delvoker"

COL_BLACK = 0
COL_NAVY = 1
COL_DARK_PURPLE = 2
COL_DARK_GREEN = 3
COL_BROWN = 4
COL_DARK_GRAY = 5
COL_LIGHT_GRAY = 6
COL_WHITE = 7
COL_RED = 8
COL_ORANGE = 9
COL_YELLOW = 10
COL_GREEN = 11
COL_BLUE = 12
COL_INDIGO = 13
COL_PINK = 14
COL_PEACH = 15

VIEW_H = 176
STATUS_Y = VIEW_H
MAX_DEPTH = 4

# Perspective frames (x1, y1, x2, y2) — each step scales by r≈0.65
# All frames share the same vanishing point (127.5, 87.5) and aspect ratio
FRAMES = [
    (0,   0,   255, 175),
    (45,  31,  210, 144),
    (74,  51,  181, 125),
    (93,  64,  163, 112),
    (105, 72,  150, 103),
]

# Wall fill colors by depth (near=bright, far=dark)
WALL_COLS = [COL_GREEN, COL_DARK_GREEN, COL_DARK_GREEN, COL_NAVY]

DUNGEON_MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 1, 1],
    [1, 0, 1, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 1],
    [1, 1, 1, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]

# N, E, S, W
DIR_VECTORS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
DIR_NAMES = ['N', 'E', 'S', 'W']


def is_wall(x, y):
    if y < 0 or y >= len(DUNGEON_MAP) or x < 0 or x >= len(DUNGEON_MAP[0]):
        return True
    return DUNGEON_MAP[y][x] == 1


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title=TITLE, fps=FPS)
        self.px = 1
        self.py = 1
        self.dir = 1  # 0=N, 1=E, 2=S, 3=W
        pyxel.run(self.update, self.draw)

    def wall_at(self, fwd, side):
        dx, dy = DIR_VECTORS[self.dir]
        rx, ry = DIR_VECTORS[(self.dir + 1) % 4]
        return is_wall(self.px + dx * fwd + rx * side,
                       self.py + dy * fwd + ry * side)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        dx, dy = DIR_VECTORS[self.dir]
        if pyxel.btnp(pyxel.KEY_UP):
            nx, ny = self.px + dx, self.py + dy
            if not is_wall(nx, ny):
                self.px, self.py = nx, ny
        if pyxel.btnp(pyxel.KEY_DOWN):
            nx, ny = self.px - dx, self.py - dy
            if not is_wall(nx, ny):
                self.px, self.py = nx, ny
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.dir = (self.dir - 1) % 4
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.dir = (self.dir + 1) % 4

    def draw_3d_view(self):
        # cls(COL_BLACK) in draw() provides the shadow base

        # Ceiling and floor: same WALL_COLS as walls, far to near
        for d in range(MAX_DEPTH - 1, -1, -1):
            fx1, fy1, fx2, fy2 = FRAMES[d]
            nfx1, nfy1, nfx2, nfy2 = FRAMES[d + 1]
            wc = WALL_COLS[d] if d < len(WALL_COLS) else COL_DARK_GRAY
            pyxel.tri(fx1, fy1, fx2,  fy1, nfx2, nfy1, wc)
            pyxel.tri(fx1, fy1, nfx1, nfy1, nfx2, nfy1, wc)
            pyxel.tri(fx1, fy2, fx2,  fy2, nfx2, nfy2, wc)
            pyxel.tri(fx1, fy2, nfx1, nfy2, nfx2, nfy2, wc)

        # Vanishing point center (darkest)
        nfx1, nfy1, nfx2, nfy2 = FRAMES[MAX_DEPTH]
        pyxel.rect(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, COL_NAVY)
        pyxel.rectb(nfx1, nfy1, nfx2 - nfx1 + 1,
                    nfy2 - nfy1 + 1, COL_DARK_GRAY)

        # Determine how far we can see (stop at first front wall)
        visible = MAX_DEPTH
        for d in range(MAX_DEPTH):
            if self.wall_at(d + 1, 0):
                visible = d + 1
                break

        # Draw far to near
        for d in range(visible - 1, -1, -1):
            fx1, fy1, fx2, fy2 = FRAMES[d]
            nfx1, nfy1, nfx2, nfy2 = FRAMES[d + 1]

            front = self.wall_at(d + 1, 0)
            left = self.wall_at(d, -1)
            right = self.wall_at(d, 1)

            wc = WALL_COLS[d] if d < len(WALL_COLS) else COL_DARK_GRAY

            # Solid wall fills
            if front:
                pyxel.rect(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, wc)
                pyxel.rectb(nfx1, nfy1, nfx2 - nfx1 + 1,
                            nfy2 - nfy1 + 1, COL_DARK_GRAY)
            if left:
                pyxel.tri(fx1, fy1, nfx1, nfy1, nfx1, nfy2, wc)
                pyxel.tri(fx1, fy1, fx1, fy2, nfx1, nfy2, wc)
                pyxel.line(nfx1, nfy1, nfx1, nfy2, COL_DARK_GRAY)
            if right:
                pyxel.tri(nfx2, nfy1, fx2, fy1, fx2, fy2, wc)
                pyxel.tri(nfx2, nfy1, nfx2, nfy2, fx2, fy2, wc)
                pyxel.line(nfx2, nfy1, nfx2, nfy2, COL_DARK_GRAY)

            # Depth diagonal lines only (shadow-unified color)
            pyxel.line(fx1, fy1, nfx1, nfy1, COL_DARK_GRAY)
            pyxel.line(fx2, fy1, nfx2, nfy1, COL_DARK_GRAY)
            pyxel.line(fx1, fy2, nfx1, nfy2, COL_DARK_GRAY)
            pyxel.line(fx2, fy2, nfx2, nfy2, COL_DARK_GRAY)

    def draw_status(self):
        pyxel.rect(0, STATUS_Y, SCREEN_W, SCREEN_H - STATUS_Y, COL_BLACK)
        pyxel.line(0, STATUS_Y, SCREEN_W - 1, STATUS_Y, COL_DARK_GRAY)
        pyxel.text(4, STATUS_Y + 4,
                   f"({self.px},{self.py}) {DIR_NAMES[self.dir]}", COL_LIGHT_GRAY)
        pyxel.text(220, STATUS_Y + 4, "B1F", COL_YELLOW)
        pyxel.text(4, STATUS_Y + 14, "Arrow:Move/Turn  Q:Quit", COL_DARK_GRAY)

    def draw(self):
        pyxel.cls(COL_NAVY)
        self.draw_3d_view()
        self.draw_status()


if __name__ == "__main__":
    App()
