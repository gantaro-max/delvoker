import pyxel

_ANIM_STEP = 0.15  # progress per frame (~7 frames to fully open at 30 FPS)


class Window:
    """Reusable UI window: double-border decoration, open animation, optional tabs.

    Usage:
        win = Window(x, y, w, h, title="TITLE", tabs=["Equip", "Items"])
        win.open()
        # each frame:
        win.update()
        win.draw(lambda cx, cy, cw, ch: pyxel.text(cx, cy, "hello", 7))
    """

    def __init__(self, x, y, w, h, title=None, tabs=None):
        self.fx, self.fy = x, y
        self.fw, self.fh = w, h
        self.title   = title
        self.tabs    = list(tabs) if tabs else []
        self.tab_idx = 0
        self._t      = 0.0    # 0 = closed … 1 = fully open
        self._going_up = False

    # ---- state ----

    @property
    def visible(self):
        return self._t > 0.0

    @property
    def ready(self):
        """True once the open animation has finished and content can be drawn."""
        return self._t >= 1.0

    def open(self):
        self._going_up = True

    def close(self):
        """Instant close — resets animation so next open() starts fresh."""
        self._going_up = False
        self._t = 0.0

    def next_tab(self):
        if self.tabs:
            self.tab_idx = (self.tab_idx + 1) % len(self.tabs)

    def prev_tab(self):
        if self.tabs:
            self.tab_idx = (self.tab_idx - 1) % len(self.tabs)

    # ---- per-frame ----

    def update(self):
        if self._going_up:
            self._t = min(1.0, self._t + _ANIM_STEP)

    def draw(self, content_fn=None):
        """Draw the window frame (and content once fully open).

        content_fn(cx, cy, cw, ch) receives the absolute screen coords of the
        usable content area inside the window chrome.
        """
        if not self.visible:
            return

        t  = self._t
        aw = max(4, int(self.fw * t))
        ah = max(4, int(self.fh * t))
        ax = self.fx + (self.fw - aw) // 2
        ay = self.fy + (self.fh - ah) // 2

        # Navy background fill
        pyxel.rect(ax, ay, aw, ah, 1)
        # Outer border (white)
        pyxel.rectb(ax, ay, aw, ah, 7)
        # Inner border (dark-gray), 2 px inset
        if aw > 6 and ah > 6:
            pyxel.rectb(ax + 2, ay + 2, aw - 4, ah - 4, 5)
        # Yellow pixel accent at each corner
        for px_, py_ in [(ax, ay), (ax+aw-1, ay), (ax, ay+ah-1), (ax+aw-1, ay+ah-1)]:
            pyxel.pset(px_, py_, 10)

        if not self.ready:
            return  # still animating — show frame only, skip content

        cx, cy = ax + 5, ay + 5
        cw = aw - 10

        # Title bar
        if self.title:
            tx = ax + (aw - len(self.title) * 4) // 2
            pyxel.text(tx, cy, self.title, 10)
            cy += 9
            pyxel.line(ax + 4, cy, ax + aw - 5, cy, 5)
            cy += 3

        # Tab bar
        if self.tabs:
            tx = cx
            for i, name in enumerate(self.tabs):
                col = 10 if i == self.tab_idx else 6
                pyxel.text(tx, cy, name, col)
                if i == self.tab_idx:
                    # Underline active tab
                    pyxel.line(tx, cy + 7, tx + len(name) * 4 - 1, cy + 7, 10)
                tx += len(name) * 4 + 8
            pyxel.text(ax + aw - 26, cy, "L/R", 5)
            cy += 11
            pyxel.line(ax + 4, cy, ax + aw - 5, cy, 5)
            cy += 3

        # Content area
        if content_fn:
            remaining_h = ah - (cy - ay) - 5
            content_fn(cx, cy, cw, remaining_h)
