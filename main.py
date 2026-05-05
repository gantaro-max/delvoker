import pyxel
import random
from data import Status, ENEMY_CATALOG

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

FRAMES = [
    (0,   0,   255, 175),
    (45,  31,  210, 144),
    (74,  51,  181, 125),
    (93,  64,  163, 112),
    (105, 72,  150, 103),
]

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

DIR_VECTORS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
DIR_NAMES = ['N', 'E', 'S', 'W']

STATE_TOWN      = 0
STATE_TOWN_SUB  = 1
STATE_DUNGEON   = 2
STATE_BATTLE_CMD = 3
STATE_BATTLE_MSG = 4
STATE_BATTLE_END = 5

ENCOUNTER_RATE = 0.3
FLEE_RATE = 0.5
COMMANDS   = ["Fight", "Flee"]
TOWN_MENU  = ["Inn", "Guild", "Shop", "Enter Dungeon"]


def is_wall(x, y):
    if y < 0 or y >= len(DUNGEON_MAP) or x < 0 or x >= len(DUNGEON_MAP[0]):
        return True
    return DUNGEON_MAP[y][x] == 1


class Player(Status):
    def __init__(self):
        super().__init__("warrior", "Hero")
        self.inventory = []
        self.gold = 0


class Enemy:
    def __init__(self, edef):
        self.name = edef.name
        self.hp = edef.hp
        self.max_hp = edef.hp
        self.weapon = edef.weapon
        self.def_ = edef.def_
        self.exp_reward = edef.exp_reward
        self.gold_reward = edef.gold_reward


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title=TITLE, fps=FPS)
        self.px = 1
        self.py = 1
        self.dir = 1

        self.player = Player()
        self.state = STATE_TOWN
        self.town_cmd_idx = 0
        self.town_sub_lines = []

        self.enemy = None
        self.cmd_idx = 0
        self.messages = []
        self.msg_idx = 0
        self.next_state = None
        self.battle_won = False

        pyxel.run(self.update, self.draw)

    def wall_at(self, fwd, side):
        dx, dy = DIR_VECTORS[self.dir]
        rx, ry = DIR_VECTORS[(self.dir + 1) % 4]
        return is_wall(self.px + dx * fwd + rx * side,
                       self.py + dy * fwd + ry * side)

    # ---- Town logic ----

    def _upd_town(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.town_cmd_idx = (self.town_cmd_idx - 1) % len(TOWN_MENU)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.town_cmd_idx = (self.town_cmd_idx + 1) % len(TOWN_MENU)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            sel = TOWN_MENU[self.town_cmd_idx]
            if sel == "Inn":
                self.player.hp = self.player.max_hp
                self.player.mp = self.player.max_mp
                self.town_sub_lines = ["Inn", "Welcome! Rest well.",
                                       "HP and MP fully restored."]
                self.state = STATE_TOWN_SUB
            elif sel == "Guild":
                self.town_sub_lines = ["Guild", "(Coming soon...)"]
                self.state = STATE_TOWN_SUB
            elif sel == "Shop":
                self.town_sub_lines = ["Shop", "(Coming soon...)"]
                self.state = STATE_TOWN_SUB
            elif sel == "Enter Dungeon":
                self.state = STATE_DUNGEON

    def _upd_town_sub(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_X):
            self.state = STATE_TOWN

    # ---- Battle logic ----

    def _start_battle(self):
        key = random.choice(list(ENEMY_CATALOG.keys()))
        self.enemy = Enemy(ENEMY_CATALOG[key])
        self.state = STATE_BATTLE_CMD
        self.cmd_idx = 0

    def _calc_dmg(self, weapon, target_def):
        return max(1, weapon.roll_damage() - target_def)

    def _player_attack(self):
        dmg = self._calc_dmg(self.player.weapon, self.enemy.def_)
        self.enemy.hp = max(0, self.enemy.hp - dmg)
        msgs = [f"{self.enemy.name}: -{dmg} HP!"]
        if self.enemy.hp <= 0:
            exp = self.enemy.exp_reward
            gold = self.enemy.gold_reward
            self.player.gold += gold
            level_ups = self.player.gain_exp(exp)
            msgs.append(f"+{exp} EXP  +{gold} Gold")
            if level_ups:
                msgs.append(f"Level Up! -> Lv{self.player.level}")
            self.battle_won = True
            self._show_msgs(msgs, STATE_BATTLE_END)
        else:
            self._enemy_turn(msgs)

    def _enemy_turn(self, msgs=None):
        if msgs is None:
            msgs = []
        dmg = self._calc_dmg(self.enemy.weapon, self.player.total_def)
        self.player.hp = max(0, self.player.hp - dmg)
        msgs.append(f"{self.player.name}: -{dmg} HP!")
        if self.player.hp <= 0:
            self.battle_won = False
            self._show_msgs(msgs, STATE_BATTLE_END)
        else:
            self._show_msgs(msgs, STATE_BATTLE_CMD)

    def _try_flee(self):
        if random.random() < FLEE_RATE:
            self._show_msgs(["Got away safely!"], STATE_DUNGEON)
        else:
            self._enemy_turn(["Couldn't escape!"])

    def _show_msgs(self, messages, next_state):
        self.messages = messages
        self.msg_idx = 0
        self.next_state = next_state
        self.state = STATE_BATTLE_MSG

    # ---- Update ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if self.state == STATE_TOWN:
            self._upd_town()
        elif self.state == STATE_TOWN_SUB:
            self._upd_town_sub()
        elif self.state == STATE_DUNGEON:
            self._upd_dungeon()
        elif self.state == STATE_BATTLE_CMD:
            self._upd_battle_cmd()
        elif self.state == STATE_BATTLE_MSG:
            self._upd_battle_msg()
        elif self.state == STATE_BATTLE_END:
            self._upd_battle_end()

    def _upd_dungeon(self):
        if pyxel.btnp(pyxel.KEY_T):
            self.state = STATE_TOWN
            return
        dx, dy = DIR_VECTORS[self.dir]
        moved = False
        if pyxel.btnp(pyxel.KEY_UP):
            nx, ny = self.px + dx, self.py + dy
            if not is_wall(nx, ny):
                self.px, self.py = nx, ny
                moved = True
        if pyxel.btnp(pyxel.KEY_DOWN):
            nx, ny = self.px - dx, self.py - dy
            if not is_wall(nx, ny):
                self.px, self.py = nx, ny
                moved = True
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.dir = (self.dir - 1) % 4
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.dir = (self.dir + 1) % 4
        if moved and random.random() < ENCOUNTER_RATE:
            self._start_battle()

    def _upd_battle_cmd(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.cmd_idx = (self.cmd_idx - 1) % len(COMMANDS)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.cmd_idx = (self.cmd_idx + 1) % len(COMMANDS)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            if self.cmd_idx == 0:
                self._player_attack()
            else:
                self._try_flee()

    def _upd_battle_msg(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self.msg_idx += 1
            if self.msg_idx >= len(self.messages):
                self.state = self.next_state
                if self.next_state in (STATE_DUNGEON, STATE_TOWN):
                    self.enemy = None

    def _upd_battle_end(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self.enemy = None
            if self.player.hp <= 0:
                # Defeat: restore and force-return to town
                self.player.hp = self.player.max_hp
                self.player.mp = self.player.max_mp
                self.state = STATE_TOWN
            else:
                self.state = STATE_DUNGEON

    # ---- Draw ----

    def draw(self):
        pyxel.cls(COL_NAVY)
        if self.state == STATE_TOWN:
            self._draw_town()
        elif self.state == STATE_TOWN_SUB:
            self._draw_town_sub()
        elif self.state == STATE_DUNGEON:
            self.draw_3d_view()
            self.draw_status()
        else:
            self._draw_battle()

    def _draw_town(self):
        pyxel.cls(COL_BLACK)

        # Title
        title = "- DELVOKER -"
        pyxel.text((SCREEN_W - len(title) * 4) // 2, 18, title, COL_YELLOW)
        sub = "Solace Town"
        pyxel.text((SCREEN_W - len(sub) * 4) // 2, 30, sub, COL_WHITE)

        # Menu box
        mx, my, mw, mh = 10, 52, 236, 78
        pyxel.rect(mx, my, mw, mh, COL_NAVY)
        pyxel.rectb(mx, my, mw, mh, COL_DARK_GRAY)
        for i, item in enumerate(TOWN_MENU):
            col = COL_YELLOW if i == self.town_cmd_idx else COL_WHITE
            cursor = ">" if i == self.town_cmd_idx else " "
            pyxel.text(mx + 8, my + 10 + i * 14, f"{cursor} {item}", col)

        # Player status box
        p = self.player
        sx, sy, sw, sh = 10, 148, 236, 62
        pyxel.rect(sx, sy, sw, sh, COL_NAVY)
        pyxel.rectb(sx, sy, sw, sh, COL_DARK_GRAY)
        pyxel.text(sx + 8, sy + 8,  f"{p.name}  Lv{p.level} {p.job.name}", COL_WHITE)
        pyxel.text(sx + 8, sy + 20, f"HP: {p.hp}/{p.max_hp}   MP: {p.mp}/{p.max_mp}", COL_GREEN)
        pyxel.text(sx + 8, sy + 32, f"EXP: {p.exp}/{p.exp_to_next}   Gold: {p.gold}", COL_YELLOW)
        pyxel.text(sx + 8, sy + 46, f"Weapon: {p.weapon.label()}", COL_PEACH)

        # Hint
        pyxel.text(6, 240, "Z/Space:Enter  Up/Down:Select  Q:Quit", COL_DARK_GRAY)

    def _draw_town_sub(self):
        pyxel.cls(COL_BLACK)

        # Facility panel
        bx, by, bw, bh = 10, 68, 236, 120
        pyxel.rect(bx, by, bw, bh, COL_NAVY)
        pyxel.rectb(bx, by, bw, bh, COL_DARK_GRAY)

        if self.town_sub_lines:
            # Facility name as title
            name = self.town_sub_lines[0]
            pyxel.text(bx + (bw - len(name) * 4) // 2, by + 10, name, COL_YELLOW)
            pyxel.line(bx + 4, by + 20, bx + bw - 4, by + 20, COL_DARK_GRAY)
            # Body lines
            for i, line in enumerate(self.town_sub_lines[1:]):
                pyxel.text(bx + 10, by + 30 + i * 14, line, COL_WHITE)

        pyxel.text(bx + bw - 54, by + bh - 12, "Z:Back", COL_DARK_GRAY)

    def _draw_battle(self):
        pyxel.cls(COL_BLACK)

        # Enemy placeholder: red rectangle centered in upper area
        ex, ey, ew, eh = 88, 28, 80, 70
        pyxel.rect(ex, ey, ew, eh, COL_RED)

        # Enemy name (centered above sprite)
        nx = ex + (ew - len(self.enemy.name) * 4) // 2
        pyxel.text(nx, ey - 10, self.enemy.name, COL_WHITE)

        # Enemy HP bar
        bx, by, bw = ex, ey + eh + 4, ew
        e_hp_f = self.enemy.hp / self.enemy.max_hp
        pyxel.rect(bx, by, bw, 4, COL_DARK_GRAY)
        pyxel.rect(bx, by, int(bw * e_hp_f), 4, COL_GREEN)
        pyxel.text(bx, by + 6, f"HP {self.enemy.hp}/{self.enemy.max_hp}", COL_LIGHT_GRAY)

        # Divider
        pyxel.line(0, 122, SCREEN_W - 1, 122, COL_DARK_GRAY)

        # Player HP (with level and job)
        p = self.player
        p_hp_f = p.hp / p.max_hp
        pyxel.text(4, 126, f"{p.name} Lv{p.level} {p.job.name}  HP {p.hp}/{p.max_hp}", COL_WHITE)
        pyxel.rect(4, 136, 100, 4, COL_DARK_GRAY)
        p_col = COL_GREEN if p_hp_f > 0.4 else (COL_ORANGE if p_hp_f > 0.2 else COL_RED)
        pyxel.rect(4, 136, int(100 * p_hp_f), 4, p_col)

        # Panel (commands / messages / result)
        panel_y = 150
        pyxel.rect(2, panel_y, SCREEN_W - 4, 88, COL_NAVY)
        pyxel.rectb(2, panel_y, SCREEN_W - 4, 88, COL_DARK_GRAY)

        if self.state == STATE_BATTLE_CMD:
            for i, cmd in enumerate(COMMANDS):
                col = COL_YELLOW if i == self.cmd_idx else COL_WHITE
                cursor = ">" if i == self.cmd_idx else " "
                pyxel.text(10, panel_y + 10 + i * 16, f"{cursor} {cmd}", col)
            pyxel.text(10, panel_y + 46, p.weapon.label(), COL_PEACH)
            pyxel.text(6, panel_y + 76, "Z/Space:OK  Up/Down:Select", COL_DARK_GRAY)

        elif self.state == STATE_BATTLE_MSG:
            if self.msg_idx < len(self.messages):
                pyxel.text(10, panel_y + 30, self.messages[self.msg_idx], COL_WHITE)
            pyxel.text(SCREEN_W - 58, panel_y + 76, "Z:Next", COL_DARK_GRAY)

        elif self.state == STATE_BATTLE_END:
            if self.battle_won:
                pyxel.text(88, panel_y + 26, "VICTORY!", COL_YELLOW)
            else:
                pyxel.text(68, panel_y + 26, "DEFEATED...", COL_RED)
                pyxel.text(44, panel_y + 42, "Returning to town...", COL_DARK_GRAY)
            pyxel.text(SCREEN_W - 82, panel_y + 76, "Z:Continue", COL_DARK_GRAY)

    def draw_3d_view(self):
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
            if self.wall_at(d + 1, 0):
                visible = d + 1
                break

        for d in range(visible - 1, -1, -1):
            fx1, fy1, fx2, fy2 = FRAMES[d]
            nfx1, nfy1, nfx2, nfy2 = FRAMES[d + 1]

            front = self.wall_at(d + 1, 0)
            left = self.wall_at(d, -1)
            right = self.wall_at(d, 1)

            wc = WALL_COLS[d] if d < len(WALL_COLS) else COL_DARK_GRAY

            if front:
                pyxel.rect(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, wc)
            if left:
                pyxel.tri(fx1, fy1, nfx1, nfy1, nfx1, nfy2, wc)
                pyxel.tri(fx1, fy1, fx1, fy2, nfx1, nfy2, wc)
            if right:
                pyxel.tri(nfx2, nfy1, fx2, fy1, fx2, fy2, wc)
                pyxel.tri(nfx2, nfy1, nfx2, nfy2, fx2, fy2, wc)
            if d < MAX_DEPTH - 1:
                if front:
                    pyxel.rectb(nfx1, nfy1, nfx2 - nfx1 + 1,
                                nfy2 - nfy1 + 1, COL_DARK_GRAY)
                pyxel.line(fx1, fy1, nfx1, nfy1, COL_DARK_GRAY)
                pyxel.line(fx2, fy1, nfx2, nfy1, COL_DARK_GRAY)
                pyxel.line(fx1, fy2, nfx1, nfy2, COL_DARK_GRAY)
                pyxel.line(fx2, fy2, nfx2, nfy2, COL_DARK_GRAY)

    def draw_status(self):
        pyxel.rect(0, STATUS_Y, SCREEN_W, SCREEN_H - STATUS_Y, COL_BLACK)
        pyxel.line(0, STATUS_Y, SCREEN_W - 1, STATUS_Y, COL_DARK_GRAY)
        p = self.player
        pyxel.text(4, STATUS_Y + 4,
                   f"{p.name}  Lv{p.level} {p.job.name}  HP:{p.hp}/{p.max_hp}",
                   COL_WHITE)
        pyxel.text(4, STATUS_Y + 16,
                   f"EXP:{p.exp}/{p.exp_to_next}  Gold:{p.gold}",
                   COL_YELLOW)
        pyxel.text(4, STATUS_Y + 28,
                   f"({self.px},{self.py}) {DIR_NAMES[self.dir]}",
                   COL_LIGHT_GRAY)
        pyxel.text(220, STATUS_Y + 28, "B1F", COL_YELLOW)
        pyxel.text(4, STATUS_Y + 40, "Arrow:Move/Turn  T:Town  Q:Quit", COL_DARK_GRAY)


if __name__ == "__main__":
    App()
