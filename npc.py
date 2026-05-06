import random
import pyxel
from data import NPC_TYPES

NPC_IDLE   = 0
NPC_WANDER = 1
NPC_CHASE  = 2

_DIR_VECTORS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

_FRAMES = [
    (0,   0,   255, 175),
    (45,  31,  210, 144),
    (74,  51,  181, 125),
    (93,  64,  163, 112),
    (105, 72,  150, 103),
]


class NPC:
    def __init__(self, npc_type_key, x, y):
        d = NPC_TYPES[npc_type_key]
        self.name            = d["name"]
        self.color           = d["color"]
        self.chase_range     = d["chase_range"]
        self.wander_interval = d["wander_interval"]
        self.enemy_key       = d["enemy_key"]
        self.x = x
        self.y = y
        self.state  = NPC_WANDER
        self._timer = random.randint(0, self.wander_interval)

    def _dist(self, px, py):
        return abs(self.x - px) + abs(self.y - py)

    def update(self, px, py, is_wall_fn):
        self._timer += 1
        dist = self._dist(px, py)

        if dist <= self.chase_range:
            self.state = NPC_CHASE
        elif self.state == NPC_CHASE and dist > self.chase_range + 1:
            self.state = NPC_WANDER

        if self.state == NPC_WANDER:
            if self._timer >= self.wander_interval:
                self._timer = 0
                dirs = list(_DIR_VECTORS)
                random.shuffle(dirs)
                for mdx, mdy in dirs:
                    nx, ny = self.x + mdx, self.y + mdy
                    if not is_wall_fn(nx, ny):
                        self.x, self.y = nx, ny
                        break

        elif self.state == NPC_CHASE:
            chase_tick = max(1, self.wander_interval // 3)
            if self._timer >= chase_tick:
                self._timer = 0
                ddx = px - self.x
                ddy = py - self.y
                if abs(ddx) >= abs(ddy):
                    moves = []
                    if ddx != 0: moves.append((1 if ddx > 0 else -1, 0))
                    if ddy != 0: moves.append((0, 1 if ddy > 0 else -1))
                else:
                    moves = []
                    if ddy != 0: moves.append((0, 1 if ddy > 0 else -1))
                    if ddx != 0: moves.append((1 if ddx > 0 else -1, 0))
                for mdx, mdy in moves:
                    nx, ny = self.x + mdx, self.y + mdy
                    if not is_wall_fn(nx, ny):
                        self.x, self.y = nx, ny
                        break

    def at_player(self, px, py):
        return self.x == px and self.y == py

    def draw(self, px, py, player_dir, is_wall_fn):
        dx, dy = _DIR_VECTORS[player_dir]
        rx, ry = _DIR_VECTORS[(player_dir + 1) % 4]

        rel_x = self.x - px
        rel_y = self.y - py
        fwd  = rel_x * dx + rel_y * dy
        side = rel_x * rx + rel_y * ry

        if fwd < 1 or fwd >= len(_FRAMES) or side != 0:
            return

        for d in range(1, fwd):
            if is_wall_fn(px + dx * d, py + dy * d):
                return

        fx1, fy1, fx2, fy2 = _FRAMES[fwd]
        fw = fx2 - fx1
        fh = fy2 - fy1
        nw = max(6, fw * 28 // 100)
        nh = max(6, fh * 55 // 100)
        cx = (fx1 + fx2) // 2
        cy = (fy1 + fy2) // 2
        nx = cx - nw // 2
        ny = cy - nh // 2 + fh // 10

        pyxel.rect(nx, ny, nw, nh, self.color)
        label = self.name[:6]
        lx = cx - len(label) * 2
        pyxel.text(lx, ny - 8, label, 7)
