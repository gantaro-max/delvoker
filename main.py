import pyxel

SCREEN_W = 256
SCREEN_H = 256
FPS = 30
TITLE = "Delvoker"

# Pyxel default 16-color palette indices (0-15)
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


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title=TITLE, fps=FPS)
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def draw(self):
        pyxel.cls(COL_BLACK)
        # "DELVOKER" = 8chars * 4px = 32px wide → center offset = 16
        pyxel.text(SCREEN_W // 2 - 16, SCREEN_H // 2 - 4, "DELVOKER", COL_WHITE)
        # "Press Q to quit" = 15chars * 4px = 60px wide → center offset = 30
        pyxel.text(SCREEN_W // 2 - 30, SCREEN_H // 2 + 8, "Press Q to quit", COL_DARK_GRAY)


if __name__ == "__main__":
    App()
