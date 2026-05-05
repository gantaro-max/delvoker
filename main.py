import pyxel
import random
from data import Status, ENEMY_CATALOG, ITEM_CATALOG
from window import Window

SCREEN_W = 256
SCREEN_H = 256
FPS = 30
TITLE = "Delvoker"

COL_BLACK      = 0
COL_NAVY       = 1
COL_DARK_PURPLE = 2
COL_DARK_GREEN  = 3
COL_BROWN       = 4
COL_DARK_GRAY   = 5
COL_LIGHT_GRAY  = 6
COL_WHITE       = 7
COL_RED         = 8
COL_ORANGE      = 9
COL_YELLOW      = 10
COL_GREEN       = 11
COL_BLUE        = 12
COL_INDIGO      = 13
COL_PINK        = 14
COL_PEACH       = 15

VIEW_H    = 176
STATUS_Y  = VIEW_H
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
DIR_NAMES   = ['N', 'E', 'S', 'W']

STATE_TOWN       = 0
STATE_TOWN_SUB   = 1
STATE_DUNGEON    = 2
STATE_BATTLE_CMD = 3
STATE_BATTLE_MSG = 4
STATE_BATTLE_END = 5
STATE_INVENTORY  = 6
STATE_INV_ACTION = 7
STATE_SHOP       = 8

INV_MAX   = 8
SHOP_KEYS = ["short_sword", "long_sword", "staff", "leather_armor", "chain_mail", "herb", "potion", "ether"]
DROP_POOL = ["short_sword", "leather_armor", "herb", "potion", "staff"]
DROP_RATE = 0.35

ENCOUNTER_RATE = 0.3
FLEE_RATE      = 0.5
COMMANDS  = ["Fight", "Flee"]
TOWN_MENU = ["Inn", "Guild", "Shop", "Enter Dungeon"]


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
        self.name        = edef.name
        self.hp          = edef.hp
        self.max_hp      = edef.hp
        self.weapon      = edef.weapon
        self.def_        = edef.def_
        self.exp_reward  = edef.exp_reward
        self.gold_reward = edef.gold_reward


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title=TITLE, fps=FPS)
        self.px  = 1
        self.py  = 1
        self.dir = 1

        self.player = Player()

        # Battle state
        self.enemy          = None
        self.cmd_idx        = 0
        self.messages       = []
        self.msg_idx        = 0
        self.next_state     = None
        self.battle_won     = False
        self.level_up_gains = []

        # Town state
        self.town_cmd_idx   = 0
        self.town_sub_lines = []

        # Inventory state
        self.inv_idx        = 0
        self.inv_action_idx = 0
        self.inv_actions    = []
        self.pre_inv_state  = STATE_TOWN

        # Shop state
        self.shop_idx = 0

        # UI Windows
        self.town_win       = Window(8,  30, 240, 100, title="- DELVOKER -")
        self.status_win     = Window(8, 143, 240,  72)
        self.sub_win        = Window(10, 62, 236, 120)
        self.battle_win     = Window(2, 150, SCREEN_W - 4, 88)
        self.inv_win        = Window(8,  10, 240, 230, title="- INVENTORY -")
        self.inv_action_win = Window(78, 96, 100,  56, title="Action")
        self.shop_win       = Window(8,  10, 240, 230, title="- SHOP -")

        self.state = None
        self._set_state(STATE_TOWN)

        pyxel.run(self.update, self.draw)

    # ---- state transitions ----

    def _set_state(self, new_state):
        self.state = new_state
        if new_state == STATE_TOWN:
            self.sub_win.close()
            self.battle_win.close()
            self.inv_win.close()
            self.inv_action_win.close()
            self.shop_win.close()
            self.town_win.open()
            self.status_win.open()
        elif new_state == STATE_TOWN_SUB:
            self.sub_win.open()
        elif new_state == STATE_DUNGEON:
            self.town_win.close()
            self.status_win.close()
            self.sub_win.close()
            self.battle_win.close()
            self.inv_win.close()
            self.inv_action_win.close()
            self.shop_win.close()
        elif new_state == STATE_INVENTORY:
            self.town_win.close()
            self.status_win.close()
            self.sub_win.close()
            self.shop_win.close()
            self.inv_action_win.close()
            self.inv_win.open()
        elif new_state == STATE_INV_ACTION:
            self.inv_action_win.open()
        elif new_state == STATE_SHOP:
            self.sub_win.close()
            self.town_win.close()
            self.status_win.close()
            self.shop_win.open()

    def wall_at(self, fwd, side):
        dx, dy = DIR_VECTORS[self.dir]
        rx, ry = DIR_VECTORS[(self.dir + 1) % 4]
        return is_wall(self.px + dx * fwd + rx * side,
                       self.py + dy * fwd + ry * side)

    # ---- Town logic ----

    def _upd_town(self):
        if pyxel.btnp(pyxel.KEY_I):
            self.pre_inv_state = STATE_TOWN
            self.inv_idx = 0
            self._set_state(STATE_INVENTORY)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.town_cmd_idx = (self.town_cmd_idx - 1) % len(TOWN_MENU)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.town_cmd_idx = (self.town_cmd_idx + 1) % len(TOWN_MENU)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            sel = TOWN_MENU[self.town_cmd_idx]
            if sel == "Inn":
                self.player.hp = self.player.max_hp
                self.player.mp = self.player.max_mp
                self.sub_win.title = "Inn"
                self.town_sub_lines = ["Welcome! Rest well.",
                                       "HP and MP fully restored."]
                self._set_state(STATE_TOWN_SUB)
            elif sel == "Guild":
                self.sub_win.title = "Guild"
                self.town_sub_lines = ["(Coming soon...)"]
                self._set_state(STATE_TOWN_SUB)
            elif sel == "Shop":
                self.shop_idx = 0
                self._set_state(STATE_SHOP)
            elif sel == "Enter Dungeon":
                self._set_state(STATE_DUNGEON)

    def _upd_town_sub(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_TOWN)

    # ---- Battle logic ----

    def _start_battle(self):
        key = random.choice(list(ENEMY_CATALOG.keys()))
        self.enemy   = Enemy(ENEMY_CATALOG[key])
        self.cmd_idx = 0
        self.battle_win.close()
        self.battle_win.open()
        self._set_state(STATE_BATTLE_CMD)

    def _calc_dmg(self, weapon, target_def):
        return max(1, weapon.roll_damage() - target_def)

    def _player_attack(self):
        dmg = self._calc_dmg(self.player.weapon, self.enemy.def_)
        self.enemy.hp = max(0, self.enemy.hp - dmg)
        msgs = [f"{self.enemy.name}: -{dmg} HP!"]
        if self.enemy.hp <= 0:
            exp  = self.enemy.exp_reward
            gold = self.enemy.gold_reward
            self.player.gold += gold
            level_ups = self.player.gain_exp(exp)
            self.level_up_gains = level_ups
            msgs.append(f"+{exp} EXP  +{gold} Gold")
            if level_ups:
                msgs.append(f"Level Up! Lv{self.player.level - len(level_ups)} -> Lv{self.player.level}")
                for lu in level_ups:
                    parts = [f"HP+{lu['hp']}"]
                    if lu["mp"]  > 0: parts.append(f"MP+{lu['mp']}")
                    if lu["str"] > 0: parts.append("STR+1")
                    if lu["def"] > 0: parts.append("DEF+1")
                    if lu["agi"] > 0: parts.append("AGI+1")
                    msgs.append("  ".join(parts))
            if random.random() < DROP_RATE:
                drop_key = random.choice(DROP_POOL)
                drop_item = ITEM_CATALOG[drop_key]
                if len(self.player.inventory) < INV_MAX:
                    self.player.inventory.append(drop_item)
                    msgs.append(f"Got: {drop_item.name}!")
                else:
                    msgs.append("Bag full! Item lost.")
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
        self.messages   = messages
        self.msg_idx    = 0
        self.next_state = next_state
        self.state      = STATE_BATTLE_MSG  # direct: no window transition

    # ---- Update ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        self.town_win.update()
        self.status_win.update()
        self.sub_win.update()
        self.battle_win.update()
        self.inv_win.update()
        self.inv_action_win.update()
        self.shop_win.update()

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
        elif self.state == STATE_INVENTORY:
            self._upd_inventory()
        elif self.state == STATE_INV_ACTION:
            self._upd_inv_action()
        elif self.state == STATE_SHOP:
            self._upd_shop()

    def _upd_dungeon(self):
        if pyxel.btnp(pyxel.KEY_T):
            self._set_state(STATE_TOWN)
            return
        if pyxel.btnp(pyxel.KEY_I):
            self.pre_inv_state = STATE_DUNGEON
            self.inv_idx = 0
            self._set_state(STATE_INVENTORY)
            return
        dx, dy = DIR_VECTORS[self.dir]
        moved  = False
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
                ns = self.next_state
                if ns in (STATE_DUNGEON, STATE_TOWN):
                    self.enemy = None
                    self._set_state(ns)
                else:
                    self.state = ns

    def _upd_battle_end(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self.enemy = None
            self.level_up_gains = []
            if self.player.hp <= 0:
                self.player.hp = self.player.max_hp
                self.player.mp = self.player.max_mp
                self._set_state(STATE_TOWN)
            else:
                self._set_state(STATE_DUNGEON)

    # ---- Inventory logic ----

    def _upd_inventory(self):
        inv = self.player.inventory
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(self.pre_inv_state)
            return
        if not inv:
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.inv_idx = (self.inv_idx - 1) % len(inv)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.inv_idx = (self.inv_idx + 1) % len(inv)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            item = inv[self.inv_idx]
            self.inv_actions = ["Use", "Drop", "Cancel"] if item.kind == "consumable" \
                               else ["Equip", "Drop", "Cancel"]
            self.inv_action_idx = 0
            self._set_state(STATE_INV_ACTION)

    def _upd_inv_action(self):
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_INVENTORY)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.inv_action_idx = (self.inv_action_idx - 1) % len(self.inv_actions)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.inv_action_idx = (self.inv_action_idx + 1) % len(self.inv_actions)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            sel = self.inv_actions[self.inv_action_idx]
            item = self.player.inventory[self.inv_idx]
            if sel == "Equip":
                self._do_equip(item)
            elif sel == "Use":
                self._do_use(item)
            elif sel == "Drop":
                self.player.inventory.remove(item)
                self.inv_idx = min(self.inv_idx, max(0, len(self.player.inventory) - 1))
            self._set_state(STATE_INVENTORY)

    def _do_equip(self, item):
        p = self.player
        if item.kind == "weapon":
            if p.weapon:
                p.inventory.append(p.weapon)
            p.weapon = item
        elif item.kind == "armor":
            if p.armor:
                p.inventory.append(p.armor)
            p.armor = item
        p.inventory.remove(item)
        self.inv_idx = min(self.inv_idx, max(0, len(p.inventory) - 1))

    def _do_use(self, item):
        p = self.player
        p.hp = min(p.max_hp, p.hp + item.hp_restore)
        p.mp = min(p.max_mp, p.mp + item.mp_restore)
        p.inventory.remove(item)
        self.inv_idx = min(self.inv_idx, max(0, len(p.inventory) - 1))

    # ---- Shop logic ----

    def _upd_shop(self):
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_TOWN)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.shop_idx = (self.shop_idx - 1) % len(SHOP_KEYS)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.shop_idx = (self.shop_idx + 1) % len(SHOP_KEYS)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            if len(self.player.inventory) >= INV_MAX:
                return
            item = ITEM_CATALOG[SHOP_KEYS[self.shop_idx]]
            if self.player.gold >= item.value:
                self.player.gold -= item.value
                self.player.inventory.append(item)

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
        elif self.state in (STATE_INVENTORY, STATE_INV_ACTION):
            self._draw_inventory()
        elif self.state == STATE_SHOP:
            self._draw_shop()
        else:
            self._draw_battle()

    def _draw_town(self):
        pyxel.cls(COL_BLACK)

        def _menu_content(cx, cy, cw, ch):
            sub = "Solace Town"
            pyxel.text(cx + (cw - len(sub) * 4) // 2, cy, sub, COL_WHITE)
            for i, item in enumerate(TOWN_MENU):
                col    = COL_YELLOW if i == self.town_cmd_idx else COL_WHITE
                cursor = ">" if i == self.town_cmd_idx else " "
                pyxel.text(cx + 4, cy + 12 + i * 14, f"{cursor} {item}", col)

        self.town_win.draw(_menu_content)

        def _status_content(cx, cy, cw, ch):
            p = self.player
            pyxel.text(cx, cy,     f"{p.name}  Lv{p.level} {p.job.name}", COL_WHITE)
            pyxel.text(cx, cy+12,  f"HP: {p.hp}/{p.max_hp}   MP: {p.mp}/{p.max_mp}", COL_GREEN)
            pyxel.text(cx, cy+24,  f"EXP: {p.exp}/{p.exp_to_next}   Gold: {p.gold}", COL_YELLOW)
            pyxel.text(cx, cy+36,  f"Weapon: {p.weapon.label()}", COL_PEACH)

        self.status_win.draw(_status_content)
        pyxel.text(6, 240, "Z/Space:Enter  Up/Down:Select  Q:Quit", COL_DARK_GRAY)

    def _draw_town_sub(self):
        pyxel.cls(COL_BLACK)

        def _sub_content(cx, cy, cw, ch):
            for i, line in enumerate(self.town_sub_lines):
                pyxel.text(cx, cy + i * 14, line, COL_WHITE)
            pyxel.text(cx + cw - 24, cy + ch - 8, "Z:Back", COL_DARK_GRAY)

        self.sub_win.draw(_sub_content)

    def _draw_battle(self):
        pyxel.cls(COL_BLACK)

        # Enemy placeholder (red rect)
        ex, ey, ew, eh = 88, 28, 80, 70
        pyxel.rect(ex, ey, ew, eh, COL_RED)
        nx = ex + (ew - len(self.enemy.name) * 4) // 2
        pyxel.text(nx, ey - 10, self.enemy.name, COL_WHITE)
        bx, by, bw_ = ex, ey + eh + 4, ew
        e_hp_f = self.enemy.hp / self.enemy.max_hp
        pyxel.rect(bx, by, bw_, 4, COL_DARK_GRAY)
        pyxel.rect(bx, by, int(bw_ * e_hp_f), 4, COL_GREEN)
        pyxel.text(bx, by + 6, f"HP {self.enemy.hp}/{self.enemy.max_hp}", COL_LIGHT_GRAY)

        pyxel.line(0, 122, SCREEN_W - 1, 122, COL_DARK_GRAY)

        p      = self.player
        p_hp_f = p.hp / p.max_hp
        pyxel.text(4, 126, f"{p.name} Lv{p.level} {p.job.name}  HP {p.hp}/{p.max_hp}", COL_WHITE)
        pyxel.rect(4, 136, 100, 4, COL_DARK_GRAY)
        p_col = COL_GREEN if p_hp_f > 0.4 else (COL_ORANGE if p_hp_f > 0.2 else COL_RED)
        pyxel.rect(4, 136, int(100 * p_hp_f), 4, p_col)

        def _panel_content(cx, cy, cw, ch):
            if self.state == STATE_BATTLE_CMD:
                for i, cmd in enumerate(COMMANDS):
                    col    = COL_YELLOW if i == self.cmd_idx else COL_WHITE
                    cursor = ">" if i == self.cmd_idx else " "
                    pyxel.text(cx, cy + i * 16, f"{cursor} {cmd}", col)
                pyxel.text(cx, cy + 40, p.weapon.label(), COL_PEACH)
                pyxel.text(6, cy + ch - 8, "Z/Space:OK  Up/Down:Select", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_MSG:
                if self.msg_idx < len(self.messages):
                    pyxel.text(cx, cy + 20, self.messages[self.msg_idx], COL_WHITE)
                pyxel.text(SCREEN_W - 58, cy + ch - 8, "Z:Next", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_END:
                if self.battle_won:
                    pyxel.text(cx + (cw - 32) // 2, cy + 8, "VICTORY!", COL_YELLOW)
                    bp = self.player
                    pyxel.text(cx, cy + 22, f"HP:{bp.hp}/{bp.max_hp}  EXP:{bp.exp}/{bp.exp_to_next}", COL_GREEN)
                    if self.level_up_gains:
                        lu = self.level_up_gains[-1]
                        parts = [f"HP+{lu['hp']}"]
                        if lu["mp"]  > 0: parts.append(f"MP+{lu['mp']}")
                        if lu["str"] > 0: parts.append("STR+1")
                        if lu["def"] > 0: parts.append("DEF+1")
                        if lu["agi"] > 0: parts.append("AGI+1")
                        pyxel.text(cx, cy + 34, "  ".join(parts), COL_PEACH)
                else:
                    pyxel.text(cx + (cw - 44) // 2, cy + 14, "DEFEATED...", COL_RED)
                    pyxel.text(cx + (cw - 80) // 2, cy + 28, "Returning to town...", COL_DARK_GRAY)
                pyxel.text(SCREEN_W - 82, cy + ch - 8, "Z:Continue", COL_DARK_GRAY)

        self.battle_win.draw(_panel_content)

    def _draw_inventory(self):
        pyxel.cls(COL_BLACK)

        def _inv_content(cx, cy, cw, ch):
            inv = self.player.inventory
            if not inv:
                pyxel.text(cx, cy + 40, "-- Empty --", COL_DARK_GRAY)
            else:
                for i, item in enumerate(inv):
                    col    = COL_YELLOW if i == self.inv_idx else COL_WHITE
                    cursor = ">" if i == self.inv_idx else " "
                    eq     = item is self.player.weapon or item is self.player.armor
                    tag    = {"weapon": "W", "armor": "A", "consumable": "C"}.get(item.kind, "?")
                    name_col = COL_GREEN if eq else col
                    pyxel.text(cx,          cy + i * 14, f"{cursor} {item.name}", name_col)
                    pyxel.text(cx + cw - 12, cy + i * 14, f"[{tag}]", COL_LIGHT_GRAY)
            p = self.player
            pyxel.text(cx, cy + ch - 16, f"Gold: {p.gold}G   {len(p.inventory)}/{INV_MAX} items", COL_YELLOW)
            pyxel.text(cx, cy + ch - 8,  "Z:Select  X:Close  [W]eap [A]rmor [C]onsumable", COL_DARK_GRAY)

        self.inv_win.draw(_inv_content)

        if self.state == STATE_INV_ACTION:
            def _action_content(cx, cy, _cw, _ch):
                for i, act in enumerate(self.inv_actions):
                    col = COL_YELLOW if i == self.inv_action_idx else COL_WHITE
                    cur = ">" if i == self.inv_action_idx else " "
                    pyxel.text(cx, cy + i * 14, f"{cur} {act}", col)
            self.inv_action_win.draw(_action_content)

    def _draw_shop(self):
        pyxel.cls(COL_BLACK)

        def _shop_content(cx, cy, cw, ch):
            for i, key in enumerate(SHOP_KEYS):
                item      = ITEM_CATALOG[key]
                col       = COL_YELLOW if i == self.shop_idx else COL_WHITE
                cursor    = ">" if i == self.shop_idx else " "
                affordable = self.player.gold >= item.value
                name_col  = col if affordable else COL_DARK_GRAY
                pyxel.text(cx,           cy + i * 14, f"{cursor} {item.name}", name_col)
                pyxel.text(cx + cw - 36, cy + i * 14, f"{item.value}G",
                           COL_YELLOW if affordable else COL_DARK_GRAY)
            p = self.player
            pyxel.text(cx, cy + ch - 16, f"Gold: {p.gold}G", COL_YELLOW)
            if len(p.inventory) >= INV_MAX:
                pyxel.text(cx + 60, cy + ch - 16, "Bag Full!", COL_RED)
            pyxel.text(cx, cy + ch - 8, "Z:Buy  X:Back", COL_DARK_GRAY)

        self.shop_win.draw(_shop_content)

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
            left  = self.wall_at(d, -1)
            right = self.wall_at(d, 1)
            wc    = WALL_COLS[d] if d < len(WALL_COLS) else COL_DARK_GRAY
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
                    pyxel.rectb(nfx1, nfy1, nfx2 - nfx1 + 1, nfy2 - nfy1 + 1, COL_DARK_GRAY)
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
        pyxel.text(4, STATUS_Y + 40, "Arrow:Move  T:Town  I:Item  Q:Quit", COL_DARK_GRAY)


if __name__ == "__main__":
    App()
