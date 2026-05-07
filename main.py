import pyxel
import random
from data import (Status, ENEMY_CATALOG, ITEM_CATALOG,
                  make_enchanted_weapon, EnchantedWeapon,
                  make_enchanted_armor, EnchantedArmor,
                  NPCMember, Party, ATTR_AFFINITY,
                  Skill, MAX_SKILLS, GrimoireItem,
                  Map, TILE_FLOOR, TILE_WALL, TILE_STAIRS, TILE_CHEST)
from window import Window
from npc import NPC

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

# Static fallback map (used only when _dungeon_map is None)
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

STATE_TOWN          = 0
STATE_TOWN_SUB      = 1
STATE_DUNGEON       = 2
STATE_BATTLE_CMD    = 3
STATE_BATTLE_MSG    = 4
STATE_BATTLE_END    = 5
STATE_INVENTORY     = 6
STATE_INV_ACTION    = 7
STATE_SHOP          = 8
STATE_BATTLE_NPC_CMD = 9
STATE_GUILD         = 10
STATE_STAT_ALLOC    = 11

INV_MAX   = 8
SHOP_KEYS = ["short_sword", "long_sword", "staff", "leather_armor", "chain_mail",
             "herb", "potion", "ether", "grimoire_fire", "grimoire_heal"]
PROMOTION_COST = 1000
WEAPON_DROP_POOL = ["short_sword", "long_sword", "staff"]
ITEM_DROP_POOL   = ["leather_armor", "herb", "potion"]
DROP_RATE        = 0.35

ENCOUNTER_RATE = 0.15
FLEE_RATE      = 0.5
COMMANDS  = ["Fight", "Flee"]
TOWN_MENU = ["Inn", "Guild", "Shop", "Stats", "Enter Dungeon"]

STAT_ALLOC_NAMES = ["STR", "DEF", "AGI", "MAG"]
STAT_ALLOC_ATTRS = ["str_", "def_", "agi", "mag"]

# Global dungeon map (set by _enter_dungeon_fresh / _next_floor)
_dungeon_map = None


def is_wall(x, y):
    if _dungeon_map is not None:
        return _dungeon_map.is_wall(x, y)
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
        self.weaknesses  = edef.weaknesses
        self.resistances = edef.resistances


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title=TITLE, fps=FPS)
        self.px  = 1
        self.py  = 1
        self.dir = 1

        self.player = Player()

        # Party (player + up to 2 NPC members)
        self.party = Party(self.player)
        demo_npc = NPCMember("warrior", "Gard", "reckless")
        self.party.add(demo_npc)

        # NPC list (replaced each dungeon entry)
        self.npcs = []

        # Battle state
        self.enemy             = None
        self.cmd_idx           = 0
        self.messages          = []
        self.msg_idx           = 0
        self.next_state        = None
        self.battle_won        = False
        self.level_up_gains    = []
        self._current_enemy_key = None
        self.enemy_telegraphing = False

        # Damage / heal popups  {"text", "x", "y", "color", "timer"}
        self.popups = []

        # Town state
        self.town_cmd_idx      = 0
        self.town_sub_lines    = []
        self._dialog_return_state = STATE_TOWN

        # Inventory state
        self.inv_idx        = 0
        self.inv_action_idx = 0
        self.inv_actions    = []
        self.pre_inv_state  = STATE_TOWN

        # Shop state
        self.shop_idx = 0

        # Guild state
        self.guild_idx = 0

        # Stat allocation
        self.stat_alloc_idx = 0

        # Dungeon
        self.dungeon_floor = 1

        # NPC command selection (unique NPCs)
        self.npc_cmd_idx      = 0
        self._npc_cmd_queue   = []
        self._round_msgs      = []
        self.current_npc_actor = None

        # Visual flash on item loss
        self.flash_timer    = 0
        self.lost_item_name = ""

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

    # ---- helpers ----

    def add_popup(self, text, x, y, color):
        self.popups.append({"text": text, "x": x, "y": y, "color": color, "timer": 20})

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
        elif new_state == STATE_GUILD:
            self.sub_win.close()
            self.town_win.close()
            self.status_win.close()
            self.shop_win.close()
            self.sub_win.open()
        elif new_state == STATE_STAT_ALLOC:
            self.sub_win.close()
            self.town_win.close()
            self.status_win.close()
            self.shop_win.close()
            self.sub_win.open()

    def wall_at(self, fwd, side):
        dx, dy = DIR_VECTORS[self.dir]
        rx, ry = DIR_VECTORS[(self.dir + 1) % 4]
        return is_wall(self.px + dx * fwd + rx * side,
                       self.py + dy * fwd + ry * side)

    # ---- Dungeon entry / floor management ----

    def _enter_dungeon_fresh(self):
        global _dungeon_map
        _dungeon_map = Map.generate_random()
        self.px = _dungeon_map.start_x
        self.py = _dungeon_map.start_y
        self.dir = 1
        _dungeon_map.visit(self.px, self.py)
        self.dungeon_floor = 1
        self._spawn_dungeon_npcs()
        self._set_state(STATE_DUNGEON)

    def _next_floor(self):
        global _dungeon_map
        self.dungeon_floor += 1
        _dungeon_map = Map.generate_random()
        self.px = _dungeon_map.start_x
        self.py = _dungeon_map.start_y
        _dungeon_map.visit(self.px, self.py)
        self._spawn_dungeon_npcs()

    def _spawn_dungeon_npcs(self):
        floor_tiles = [
            (x, y)
            for y in range(_dungeon_map.height)
            for x in range(_dungeon_map.width)
            if _dungeon_map.tile_at(x, y) == TILE_FLOOR
            and not (x == self.px and y == self.py)
        ]
        npc_pool = ["slime", "goblin", "skeleton"]
        count = random.randint(2, 4)
        positions = random.sample(floor_tiles, min(count, len(floor_tiles)))
        self.npcs = [NPC(random.choice(npc_pool), px, py) for px, py in positions]

    def _open_chest(self):
        global _dungeon_map
        _dungeon_map.set_tile(self.px, self.py, TILE_FLOOR)
        if len(self.player.inventory) >= INV_MAX:
            lines = ["A chest! Bag is full.", "Item was left behind..."]
        else:
            if random.random() < 0.6:
                drop_key = random.choice(WEAPON_DROP_POOL)
                item = make_enchanted_weapon(drop_key)
            else:
                drop_key = random.choice(ITEM_DROP_POOL)
                base = ITEM_CATALOG[drop_key]
                item = make_enchanted_armor(drop_key) if base.kind == "armor" else base.clone()
            self.player.inventory.append(item)
            name = item.label() if hasattr(item, "label") else item.name
            lines = ["Found a chest!", f"Got: {name}!"]
        self.sub_win.title = "CHEST"
        self.town_sub_lines = lines
        self._dialog_return_state = STATE_DUNGEON
        self._set_state(STATE_TOWN_SUB)

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
                self._dialog_return_state = STATE_TOWN
                self._set_state(STATE_TOWN_SUB)
            elif sel == "Guild":
                self.guild_idx = 0
                self._set_state(STATE_GUILD)
            elif sel == "Shop":
                self.shop_idx = 0
                self._set_state(STATE_SHOP)
            elif sel == "Stats":
                self.stat_alloc_idx = 0
                self._set_state(STATE_STAT_ALLOC)
            elif sel == "Enter Dungeon":
                self._enter_dungeon_fresh()

    def _upd_town_sub(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_X):
            ret = self._dialog_return_state
            self._dialog_return_state = STATE_TOWN
            self._set_state(ret)

    # ---- Stat allocation logic ----

    def _upd_stat_alloc(self):
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_TOWN)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.stat_alloc_idx = (self.stat_alloc_idx - 1) % len(STAT_ALLOC_NAMES)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.stat_alloc_idx = (self.stat_alloc_idx + 1) % len(STAT_ALLOC_NAMES)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            p = self.player
            if p.bonus_points > 0:
                attr = STAT_ALLOC_ATTRS[self.stat_alloc_idx]
                setattr(p, attr, getattr(p, attr) + 1)
                p.bonus_points -= 1

    # ---- Battle logic ----

    def _start_battle(self, enemy_key=None):
        key = enemy_key if enemy_key else random.choice(list(ENEMY_CATALOG.keys()))
        self.enemy              = Enemy(ENEMY_CATALOG[key])
        self._current_enemy_key = key
        self.enemy_telegraphing = False
        self.cmd_idx = 0
        self.battle_win.close()
        self.battle_win.open()
        self._set_state(STATE_BATTLE_CMD)

    def _calc_dmg(self, weapon, target_def, target=None):
        base = max(1, weapon.roll_damage() - target_def)
        attr = getattr(weapon, "attribute", None)
        if attr and target:
            if attr in target.weaknesses:
                return max(1, int(base * 1.5))
            if attr in target.resistances:
                return max(1, int(base * 0.5))
            cntr = ATTR_AFFINITY.get(attr)
            if cntr and cntr in target.resistances:
                return max(1, int(base * 1.5))
            if attr == "holy":
                return max(1, int(base * 1.2))
        return base

    def _get_enemy_target(self):
        """Select attack target based on enemy AI type."""
        alive = self.party.alive
        if not alive:
            return self.player
        edef = ENEMY_CATALOG.get(self._current_enemy_key) if self._current_enemy_key else None
        ai_type = edef.ai_type if edef else "normal"
        if ai_type == "ranged":
            return max(alive, key=lambda m: m.agi)
        if ai_type == "support":
            return min(alive, key=lambda m: m.hp)
        return alive[0]  # normal: attack first (player)

    def _npc_combat_action(self, npc, msgs):
        if random.random() < 0.25:
            msgs.append(f"{npc.name} acts on their own!")
            p = npc.personality
            if p == "reckless":
                dmg = self._calc_dmg(npc.weapon, self.enemy.def_, self.enemy)
                self.enemy.hp = max(0, self.enemy.hp - dmg)
                msgs.append(f"[Reckless] {npc.name} attacks wildly! {self.enemy.name}: -{dmg} HP!")
            elif p == "cowardly":
                msgs.append(f"[Cowardly] {npc.name} hesitates and does nothing!")
            elif p == "selfish":
                msgs.append(f"[Selfish] {npc.name} tends to their own wounds! (skipped)")
            else:
                dmg = self._calc_dmg(npc.weapon, self.enemy.def_, self.enemy)
                self.enemy.hp = max(0, self.enemy.hp - dmg)
                msgs.append(f"{npc.name} attacks! {self.enemy.name}: -{dmg} HP!")
        else:
            dmg = self._calc_dmg(npc.weapon, self.enemy.def_, self.enemy)
            self.enemy.hp = max(0, self.enemy.hp - dmg)
            msgs.append(f"{npc.name} attacks! {self.enemy.name}: -{dmg} HP!")

    def _handle_victory(self, msgs):
        exp  = self.enemy.exp_reward
        gold = self.enemy.gold_reward
        self.player.gold += gold
        level_ups = self.player.gain_exp(exp)
        self.level_up_gains = level_ups
        msgs.append(f"+{exp} EXP  +{gold} Gold")
        if level_ups:
            msgs.append(f"Level Up! Lv{self.player.level - len(level_ups)} -> Lv{self.player.level}")
            msgs.append(f"+3 Bonus Points! (Total: {self.player.bonus_points})")
            for lu in level_ups:
                parts = [f"HP+{lu['hp']}"]
                if lu["mp"]  > 0: parts.append(f"MP+{lu['mp']}")
                if lu["str"] > 0: parts.append("STR+1")
                if lu["def"] > 0: parts.append("DEF+1")
                if lu["agi"] > 0: parts.append("AGI+1")
                msgs.append("  ".join(parts))
        if random.random() < DROP_RATE:
            if random.random() < 0.6:
                drop_key  = random.choice(WEAPON_DROP_POOL)
                drop_item = make_enchanted_weapon(drop_key)
            else:
                drop_key  = random.choice(ITEM_DROP_POOL)
                base_item = ITEM_CATALOG[drop_key]
                if base_item.kind == "armor":
                    drop_item = make_enchanted_armor(drop_key)
                else:
                    drop_item = base_item.clone()
            if len(self.player.inventory) < INV_MAX:
                self.player.inventory.append(drop_item)
                msgs.append(f"Got: {drop_item.label() if hasattr(drop_item, 'label') else drop_item.name}!")
            else:
                msgs.append("Bag full! Item lost.")
        self.battle_won = True
        self._show_msgs(msgs, STATE_BATTLE_END)

    def _run_auto_and_enemy(self, msgs):
        for npc in self.party.alive[1:]:
            if getattr(npc, "is_unique", False):
                continue
            if self.enemy.hp <= 0:
                break
            self._npc_combat_action(npc, msgs)
        if self.enemy.hp <= 0:
            self._handle_victory(msgs)
        else:
            self._enemy_turn(msgs)

    def _player_attack(self):
        dmg = self._calc_dmg(self.player.weapon, self.enemy.def_, self.enemy)
        self.enemy.hp = max(0, self.enemy.hp - dmg)

        attr = getattr(self.player.weapon, "attribute", None)
        popup_col = COL_YELLOW if (attr and attr in self.enemy.weaknesses) else COL_WHITE
        self.add_popup(f"-{dmg}", 116, 68, popup_col)

        msgs = [f"{self.enemy.name}: -{dmg} HP!"]
        if self.enemy.hp <= 0:
            self._handle_victory(msgs)
            return
        self._round_msgs = msgs
        self._npc_cmd_queue = [m for m in self.party.alive[1:]
                               if getattr(m, "is_unique", False)]
        if self._npc_cmd_queue:
            self.current_npc_actor = self._npc_cmd_queue.pop(0)
            self.npc_cmd_idx = 0
            self.state = STATE_BATTLE_NPC_CMD
        else:
            self._run_auto_and_enemy(msgs)

    def _calc_item_loss(self):
        p = self.player
        losable = list(p.inventory)
        if p.weapon and p.weapon.name != "Old Dagger":
            losable.append(p.weapon)
        if p.armor:
            losable.append(p.armor)
        if not losable:
            return ""
        lost = random.choice(losable)
        name = lost.label() if hasattr(lost, "label") else lost.name
        if lost in p.inventory:
            p.inventory.remove(lost)
        elif lost is p.weapon:
            p.weapon = ITEM_CATALOG["old_dagger"]
        elif lost is p.armor:
            p.armor = None
        return name

    def _enemy_turn(self, msgs=None):
        if msgs is None:
            msgs = []
        edef = ENEMY_CATALOG.get(self._current_enemy_key) if self._current_enemy_key else None

        # Boss telegraph: show warning turn before power attack
        if edef and edef.telegraph_message and not self.enemy_telegraphing and random.random() < 0.3:
            self.enemy_telegraphing = True
            msgs.append(edef.telegraph_message)
            self._show_msgs(msgs, STATE_BATTLE_CMD)
            return

        power_mult = 2 if self.enemy_telegraphing else 1
        self.enemy_telegraphing = False

        target = self._get_enemy_target()
        base_dmg = self._calc_dmg(self.enemy.weapon, target.total_def, target)
        dmg = int(base_dmg * power_mult)
        target.hp = max(0, target.hp - dmg)
        if power_mult > 1:
            msgs.append(f"[POWER] {target.name}: -{dmg} HP!")
        else:
            msgs.append(f"{target.name}: -{dmg} HP!")

        # Popup for incoming damage
        self.add_popup(f"-{dmg}", 46, 126, COL_RED)

        # Status infliction
        if edef and edef.inflict_status and random.random() < edef.inflict_chance:
            inf = edef.inflict_status
            target.status_effects[inf] = max(target.status_effects.get(inf, 0), 3)
            msgs.append(f"{target.name} is {inf}ed!")

        # Poison damage at end of turn
        for member in list(self.party.alive):
            turns = member.status_effects.get("poison", 0)
            if turns > 0:
                pdmg = 2
                member.hp = max(0, member.hp - pdmg)
                msgs.append(f"[Poison] {member.name}: -{pdmg} HP!")
                member.status_effects["poison"] = turns - 1

        if self.party.is_wiped_out:
            self.battle_won = False
            self.lost_item_name = self._calc_item_loss()
            if self.lost_item_name:
                msgs.append(f"ITEM LOST: {self.lost_item_name}...")
            self.flash_timer = 20
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
        self.state      = STATE_BATTLE_MSG

    # ---- Update ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Tick popups
        self.popups = [p for p in self.popups if p["timer"] > 0]
        for p in self.popups:
            p["timer"] -= 1

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
        elif self.state == STATE_BATTLE_NPC_CMD:
            self._upd_battle_npc_cmd()
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
        elif self.state == STATE_GUILD:
            self._upd_guild()
        elif self.state == STATE_STAT_ALLOC:
            self._upd_stat_alloc()

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
        if moved:
            if _dungeon_map is not None:
                _dungeon_map.visit(self.px, self.py)
            tile = _dungeon_map.tile_at(self.px, self.py) if _dungeon_map else 0
            if tile == TILE_STAIRS:
                self._next_floor()
                return
            if tile == TILE_CHEST:
                self._open_chest()
                return
            for npc in self.npcs:
                if npc.at_player(self.px, self.py):
                    self.npcs.remove(npc)
                    self._start_battle(npc.enemy_key)
                    return
            if random.random() < ENCOUNTER_RATE:
                self._start_battle()
                return

        for npc in self.npcs:
            npc.update(self.px, self.py, is_wall)
            if npc.at_player(self.px, self.py):
                self.npcs.remove(npc)
                self._start_battle(npc.enemy_key)
                return

    def _upd_battle_npc_cmd(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.npc_cmd_idx = (self.npc_cmd_idx - 1) % len(COMMANDS)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.npc_cmd_idx = (self.npc_cmd_idx + 1) % len(COMMANDS)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            npc = self.current_npc_actor
            if self.npc_cmd_idx == 0:  # Fight
                dmg = self._calc_dmg(npc.weapon, self.enemy.def_, self.enemy)
                self.enemy.hp = max(0, self.enemy.hp - dmg)
                self._round_msgs.append(f"{npc.name} attacks! {self.enemy.name}: -{dmg} HP!")
            else:  # Retreat
                self._round_msgs.append(f"{npc.name} holds back.")

            if self.enemy.hp <= 0:
                self._handle_victory(self._round_msgs)
            elif self._npc_cmd_queue:
                self.current_npc_actor = self._npc_cmd_queue.pop(0)
                self.npc_cmd_idx = 0
            else:
                self._run_auto_and_enemy(self._round_msgs)

    def _upd_guild(self):
        npc_members = [m for m in self.party.members[1:] if isinstance(m, NPCMember)]
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_TOWN)
            return
        if not npc_members:
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                self._set_state(STATE_TOWN)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.guild_idx = (self.guild_idx - 1) % len(npc_members)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.guild_idx = (self.guild_idx + 1) % len(npc_members)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            npc = npc_members[self.guild_idx]
            if npc.is_unique:
                return
            if self.player.gold >= PROMOTION_COST:
                self.player.gold -= PROMOTION_COST
                npc.is_unique = True

    def _upd_battle_cmd(self):
        # Stun: skip player action
        if self.player.status_effects.get("stun", 0) > 0:
            self.player.status_effects["stun"] -= 1
            msgs = [f"[Stunned] {self.player.name} cannot move!"]
            self._run_auto_and_enemy(msgs)
            return
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
            if self.party.is_wiped_out:
                for m in self.party.members:
                    m.hp = m.max_hp
                    m.mp = m.max_mp
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
            usable = item.kind == "consumable" or isinstance(item, GrimoireItem)
            self.inv_actions = ["Use", "Drop", "Cancel"] if usable \
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
        if isinstance(item, GrimoireItem):
            new_skill = Skill(item.skill_name, item.mp_cost, item.effect_type, item.power)
            if len(p.skills) >= MAX_SKILLS:
                p.skills.pop(0)
            p.skills.append(new_skill)
        else:
            heal_hp = min(p.max_hp - p.hp, item.hp_restore)
            p.hp = min(p.max_hp, p.hp + item.hp_restore)
            p.mp = min(p.max_mp, p.mp + item.mp_restore)
            if heal_hp > 0:
                self.add_popup(f"+{heal_hp}", 46, 130, COL_GREEN)
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
                self.player.inventory.append(item.clone())

    # ---- Draw ----

    def draw(self):
        pyxel.cls(COL_NAVY)
        if self.state == STATE_TOWN:
            self._draw_town()
        elif self.state == STATE_TOWN_SUB:
            self._draw_town_sub()
        elif self.state == STATE_DUNGEON:
            self.draw_3d_view()
            self.draw_npcs()
            self.draw_status()
            self.draw_minimap()
        elif self.state in (STATE_INVENTORY, STATE_INV_ACTION):
            self._draw_inventory()
        elif self.state == STATE_SHOP:
            self._draw_shop()
        elif self.state == STATE_GUILD:
            self._draw_guild()
        elif self.state == STATE_STAT_ALLOC:
            self._draw_stat_alloc()
        else:
            self._draw_battle()
        if self.flash_timer > 10:
            pyxel.rect(0, 0, SCREEN_W, SCREEN_H, COL_RED)

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
            if p.bonus_points > 0:
                pyxel.text(cx, cy+48, f"Bonus Points: {p.bonus_points}  (Stats menu)", COL_ORANGE)

        self.status_win.draw(_status_content)
        pyxel.text(6, 240, "Z/Space:Enter  Up/Down:Select  Q:Quit", COL_DARK_GRAY)

    def _draw_town_sub(self):
        pyxel.cls(COL_BLACK)

        def _sub_content(cx, cy, cw, ch):
            for i, line in enumerate(self.town_sub_lines):
                pyxel.text(cx, cy + i * 14, line, COL_WHITE)
            pyxel.text(cx + cw - 24, cy + ch - 8, "Z:Back", COL_DARK_GRAY)

        self.sub_win.draw(_sub_content)

    def _draw_stat_alloc(self):
        pyxel.cls(COL_BLACK)

        def _content(cx, cy, cw, ch):
            p = self.player
            pyxel.text(cx, cy, "== STATUS ALLOC ==", COL_YELLOW)
            pts_col = COL_GREEN if p.bonus_points > 0 else COL_DARK_GRAY
            pyxel.text(cx, cy + 12, f"Points: {p.bonus_points}", pts_col)
            for i, (name, attr) in enumerate(zip(STAT_ALLOC_NAMES, STAT_ALLOC_ATTRS)):
                cursor = ">" if i == self.stat_alloc_idx else " "
                val = getattr(p, attr)
                col = COL_YELLOW if i == self.stat_alloc_idx else COL_WHITE
                pyxel.text(cx, cy + 28 + i * 14, f"{cursor} {name}: {val}", col)
            pyxel.text(cx, cy + ch - 8, "Z:Spend Point  X:Done", COL_DARK_GRAY)

        self.sub_win.draw(_content)

    def _draw_battle(self):
        pyxel.cls(COL_BLACK)

        # Enemy area
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

        # Status effect icons
        icon_x = 108
        if p.status_effects.get("poison", 0) > 0:
            pyxel.text(icon_x, 134, "[P]", COL_GREEN)
            icon_x += 16
        if p.status_effects.get("stun", 0) > 0:
            pyxel.text(icon_x, 134, "[S]", COL_YELLOW)

        # NPC HP
        for i, npc in enumerate(self.party.members[1:]):
            npc_col = COL_GREEN if npc.hp > npc.max_hp * 0.4 else (COL_ORANGE if npc.hp > 0 else COL_RED)
            pyxel.text(4 + i * 128, 142, f"{npc.name[:6]} HP:{npc.hp}/{npc.max_hp}", npc_col)
            npc_icon_x = 4 + i * 128 + 80
            if npc.status_effects.get("poison", 0) > 0:
                pyxel.text(npc_icon_x, 142, "[P]", COL_GREEN)
                npc_icon_x += 16
            if npc.status_effects.get("stun", 0) > 0:
                pyxel.text(npc_icon_x, 142, "[S]", COL_YELLOW)

        def _panel_content(cx, cy, cw, ch):
            if self.state == STATE_BATTLE_CMD:
                for i, cmd in enumerate(COMMANDS):
                    col    = COL_YELLOW if i == self.cmd_idx else COL_WHITE
                    cursor = ">" if i == self.cmd_idx else " "
                    pyxel.text(cx, cy + i * 16, f"{cursor} {cmd}", col)
                pyxel.text(cx, cy + 40, p.weapon.label(), COL_PEACH)
                if p.skills:
                    skill_names = "  ".join(s.name[:8] for s in p.skills)
                    pyxel.text(cx, cy + 52, f"Skills: {skill_names}", COL_INDIGO)
                pyxel.text(6, cy + ch - 8, "Z/Space:OK  Up/Down:Select", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_NPC_CMD:
                npc = self.current_npc_actor
                tag = "[Unique]" if npc.is_unique else ""
                pyxel.text(cx, cy - 8, f"{npc.name} {tag}", COL_PEACH)
                for i, cmd in enumerate(COMMANDS):
                    col    = COL_YELLOW if i == self.npc_cmd_idx else COL_WHITE
                    cursor = ">" if i == self.npc_cmd_idx else " "
                    pyxel.text(cx, cy + i * 16, f"{cursor} {cmd}", col)
                pyxel.text(cx, cy + 40, npc.weapon.label(), COL_PEACH)
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

        # Damage / heal popups (float upward)
        for pop in self.popups:
            float_y = pop["y"] - (20 - pop["timer"])
            pyxel.text(pop["x"], float_y, pop["text"], pop["color"])

    def _draw_inventory(self):
        pyxel.cls(COL_BLACK)

        def _inv_content(cx, cy, cw, ch):
            inv = self.player.inventory
            if not inv:
                pyxel.text(cx, cy + 40, "-- Empty --", COL_DARK_GRAY)
            else:
                for i, item in enumerate(inv):
                    cursor = ">" if i == self.inv_idx else " "
                    eq     = item is self.player.weapon or item is self.player.armor
                    tag    = {"weapon": "W", "armor": "A", "consumable": "C"}.get(item.kind, "?")
                    if eq:
                        name_col = COL_GREEN
                    elif isinstance(item, EnchantedWeapon):
                        name_col = {
                            "cursed": COL_DARK_PURPLE,
                            "rare":   COL_ORANGE,
                            "magic":  COL_YELLOW,
                        }.get(item.rarity, COL_WHITE)
                    elif isinstance(item, EnchantedArmor):
                        name_col = COL_YELLOW if item.rarity == "magic" else COL_WHITE
                    else:
                        name_col = COL_WHITE
                    display  = item.label() if hasattr(item, "label") else item.name
                    pyxel.text(cx,           cy + i * 14, f"{cursor} {display}", name_col)
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

    def _draw_guild(self):
        def _guild_content(cx, cy, cw, ch):
            pyxel.text(cx, cy, "== GUILD ==", COL_YELLOW)
            npcs = [m for m in self.party.members if isinstance(m, NPCMember)]
            if not npcs:
                pyxel.text(cx, cy + 16, "No NPC in party.", COL_DARK_GRAY)
            else:
                for i, npc in enumerate(npcs):
                    cursor = ">" if i == self.guild_idx else " "
                    if npc.is_unique:
                        tag = "(Unique)"
                        col = COL_ORANGE
                        cost_str = "------"
                    else:
                        tag = f"1000G"
                        affordable = self.player.gold >= PROMOTION_COST
                        col = COL_WHITE if affordable else COL_DARK_GRAY
                        cost_str = tag
                    pyxel.text(cx,           cy + 16 + i * 14, f"{cursor} {npc.name} [{npc.job.name}]", col)
                    pyxel.text(cx + cw - 40, cy + 16 + i * 14, cost_str, COL_YELLOW if not npc.is_unique else COL_ORANGE)
            pyxel.text(cx, cy + ch - 16, f"Gold: {self.player.gold}G", COL_YELLOW)
            pyxel.text(cx, cy + ch - 8,  "Z:Promote  X:Back", COL_DARK_GRAY)
        self.sub_win.draw(_guild_content)

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

    def draw_npcs(self):
        for npc in self.npcs:
            npc.draw(self.px, self.py, self.dir, is_wall)

    def draw_minimap(self):
        if _dungeon_map is None:
            return
        m = _dungeon_map
        # 1px per tile, placed at bottom-right of dungeon view
        ox = SCREEN_W - m.width - 2   # 234 for width=20
        oy = VIEW_H   - m.height - 2  # 154 for height=20
        # Background
        pyxel.rect(ox - 1, oy - 1, m.width + 2, m.height + 2, COL_BLACK)
        for ty in range(m.height):
            for tx in range(m.width):
                tile = m.tile_at(tx, ty)
                if tile == TILE_WALL:
                    continue
                if not m.visited[ty][tx]:
                    continue
                if tx == self.px and ty == self.py:
                    col = COL_WHITE
                elif tile == TILE_STAIRS:
                    col = COL_YELLOW
                elif tile == TILE_CHEST:
                    col = COL_ORANGE
                else:
                    col = COL_DARK_GRAY
                pyxel.pset(ox + tx, oy + ty, col)

    def draw_status(self):
        pyxel.rect(0, STATUS_Y, SCREEN_W, SCREEN_H - STATUS_Y, COL_BLACK)
        pyxel.line(0, STATUS_Y, SCREEN_W - 1, STATUS_Y, COL_DARK_GRAY)
        p = self.player
        pyxel.text(4, STATUS_Y + 4,
                   f"{p.name}  Lv{p.level} {p.job.name}  HP:{p.hp}/{p.max_hp}",
                   COL_WHITE)
        gold_str = f"Gold:{p.gold}G"
        pyxel.text(SCREEN_W - 4 - len(gold_str) * 4, STATUS_Y + 4, gold_str, COL_YELLOW)
        status_info = f"EXP:{p.exp}/{p.exp_to_next}"
        if p.bonus_points > 0:
            status_info += f"  BP:{p.bonus_points}"
        pyxel.text(4, STATUS_Y + 16, status_info, COL_YELLOW)
        pyxel.text(4, STATUS_Y + 28,
                   f"({self.px},{self.py}) {DIR_NAMES[self.dir]}",
                   COL_LIGHT_GRAY)
        floor_str = f"B{self.dungeon_floor}F"
        pyxel.text(SCREEN_W - 4 - len(floor_str) * 4, STATUS_Y + 28, floor_str, COL_YELLOW)
        pyxel.text(4, STATUS_Y + 40, "Arrow:Move  T:Town  I:Item  Q:Quit", COL_DARK_GRAY)


if __name__ == "__main__":
    App()
