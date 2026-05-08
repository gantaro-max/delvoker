import pyxel
import random
import json
from pathlib import Path
from data import (Status, ENEMY_CATALOG, ITEM_CATALOG, JOBS,
                  WeaponItem, ArmorItem, ConsumableItem,
                  make_enchanted_weapon, EnchantedWeapon,
                  make_enchanted_armor, EnchantedArmor,
                  NPCMember, Party, ATTR_AFFINITY,
                  Skill, MAX_SKILLS, GrimoireItem,
                  Map, TILE_FLOOR, TILE_WALL, TILE_STAIRS, TILE_CHEST,
                  TILE_TRAP_SPIKE, TILE_TRAP_POISON, TILE_GRAVE, TILE_LOCKED_DOOR,
                  TILE_FOUNTAIN, TILE_MERCHANT, Grave)
from window import Window
from npc import NPC

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
MAX_FLOOR = 10

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
DIR_NAMES = ['N', 'E', 'S', 'W']

STATE_TOWN = 0
STATE_TOWN_SUB = 1
STATE_DUNGEON = 2
STATE_BATTLE_CMD = 3
STATE_BATTLE_MSG = 4
STATE_BATTLE_END = 5
STATE_INVENTORY = 6
STATE_INV_ACTION = 7
STATE_SHOP = 8
STATE_BATTLE_NPC_CMD = 9
STATE_GUILD = 10
STATE_STAT_ALLOC = 11
STATE_BATTLE_TARGET_PART = 12
STATE_REVIVE = 13
STATE_INV_GIVE_NPC = 14
STATE_HOME = 15
STATE_ENDING = 16
STATE_DUNGEON_SKILL = 17
STATE_DUNGEON_SHOP = 18
STATE_TITLE = 19
STATE_JOB_SELECT = 20

SAVE_FILE = "delvoker_save.json"

INV_MAX = 8
SHOP_KEYS = ["short_sword", "long_sword", "staff", "leather_armor", "chain_mail",
             "herb", "potion", "ether", "antidote", "scroll_mapping",
             "grimoire_fire", "grimoire_heal", "grimoire_ice", "grimoire_poison", "grimoire_return"]
MERCHANT_KEYS = ["elixir", "potion", "ether", "antidote", "holy_scroll", "grimoire_heal"]
PROMOTION_COST = 1000
DROP_RATE = 0.35

# Tier-based drop pools keyed by floor range (1-indexed upper bound inclusive)
_DROP_TIERS = [
    (3,  ["old_dagger", "short_sword", "staff"],              ["leather_armor", "herb", "potion"]),
    (6,  ["long_sword", "chain_mail"],                        ["potion", "ether", "grimoire_ice"]),
    (10, ["steel_sword", "mithril_sword", "steel_plate"],     ["ether", "grimoire_poison"]),
]

def _drop_pools(floor):
    """Return (weapon_pool, item_pool) for the given dungeon floor."""
    for cap, wp, ip in _DROP_TIERS:
        if floor <= cap:
            return wp, ip
    return _DROP_TIERS[-1][1], _DROP_TIERS[-1][2]

# Tier-based random encounter pools
_ENCOUNTER_TIERS = [
    (3,  ["slime", "bat", "goblin"]),
    (6,  ["skeleton", "goblin", "wraith"]),
    (10, ["golem", "wyvern", "wraith"]),
]

def _encounter_pool(floor):
    for cap, pool in _ENCOUNTER_TIERS:
        if floor <= cap:
            return pool
    return _ENCOUNTER_TIERS[-1][1]

ENCOUNTER_RATE = 0.15
FLEE_RATE = 0.5
COMMANDS = ["Fight", "Flee"]
TOWN_MENU = ["Inn", "Guild", "Shop", "Stats", "Revive", "Home", "Enter Dungeon"]

STAT_ALLOC_NAMES = ["STR", "DEF", "AGI", "MAG"]
STAT_ALLOC_ATTRS = ["str_", "def_", "agi", "mag"]

HOME_MENU = ["Warehouse", "Renovate", "Training", "Back"]
HOME_TRAIN_STATS = ["STR", "DEF", "MAG"]
HOME_TRAIN_ATTRS = ["str", "def", "mag"]
HOME_RENOVATE_COSTS = [500, 1000, 2000, 4000, 8000]
HOME_RENOVATE_SLOTS = 5

# BGM zone mapping: state → music index (0=town, 1=dungeon, 2=battle, -1=stop)
_BGM_ZONES = {
    STATE_TITLE: 0, STATE_JOB_SELECT: 0,
    STATE_TOWN: 0, STATE_TOWN_SUB: 0, STATE_GUILD: 0,
    STATE_STAT_ALLOC: 0, STATE_SHOP: 0, STATE_HOME: 0, STATE_REVIVE: 0,
    STATE_DUNGEON: 1, STATE_DUNGEON_SKILL: 1, STATE_DUNGEON_SHOP: 1,
    STATE_BATTLE_CMD: 2, STATE_BATTLE_MSG: 2, STATE_BATTLE_END: 2,
    STATE_BATTLE_NPC_CMD: 2, STATE_BATTLE_TARGET_PART: 2,
    STATE_ENDING: -1,
}

# Global dungeon map (set by _enter_dungeon_fresh / _next_floor)
_dungeon_map = None


def is_wall(x, y):
    if _dungeon_map is not None:
        return _dungeon_map.is_wall(x, y)
    if y < 0 or y >= len(DUNGEON_MAP) or x < 0 or x >= len(DUNGEON_MAP[0]):
        return True
    return DUNGEON_MAP[y][x] == 1


class Player(Status):
    def __init__(self, job_key="warrior"):
        super().__init__(job_key, "Hero")
        self.inventory = []
        self.gold = 0
        self.warehouse = []
        self.warehouse_max = 10
        self.perm_stats = {"str": 0, "def": 0, "mag": 0}

    @property
    def total_def(self):
        bonus = self.armor.def_bonus if self.armor else 0
        return self.def_ + bonus + self.perm_stats["def"]


class Enemy:
    def __init__(self, edef):
        self.name = edef.name
        self.hp = edef.hp
        self.max_hp = edef.hp
        self.weapon = edef.weapon
        self.def_ = edef.def_
        self.exp_reward = edef.exp_reward
        self.gold_reward = edef.gold_reward
        self.weaknesses = edef.weaknesses
        self.resistances = edef.resistances
        self.parts = edef.parts
        self.part_hps = {p["name"]: max(
            1, int(edef.hp * p["hp_ratio"])) for p in edef.parts}
        self.broken_parts = set()


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title=TITLE, fps=FPS)
        self.px = 1
        self.py = 1
        self.dir = 1

        self.player = Player()

        # Party (player + up to 2 NPC members)
        self.party = Party(self.player)
        demo_npc = NPCMember("warrior", "Gard", "reckless")
        self.party.add(demo_npc)

        # NPC list (replaced each dungeon entry)
        self.npcs = []

        # Battle state
        self.enemy = None
        self.cmd_idx = 0
        self.messages = []
        self.msg_idx = 0
        self.next_state = None
        self.battle_won = False
        self.level_up_gains = []
        self._current_enemy_key = None
        self.enemy_telegraphing = False

        # Damage / heal popups  {"text", "x", "y", "color", "timer"}
        self.popups = []

        # Town state
        self.town_cmd_idx = 0
        self.town_sub_lines = []
        self._dialog_return_state = STATE_TOWN

        # Inventory state
        self.inv_idx = 0
        self.inv_action_idx = 0
        self.inv_actions = []
        self.pre_inv_state = STATE_TOWN

        # Shop state
        self.shop_idx = 0

        # Guild state
        self.guild_idx = 0

        # Stat allocation
        self.stat_alloc_idx = 0

        # Dungeon
        self.dungeon_floor = 1

        # Part target selection
        self.part_idx = 0
        self._part_targets = []

        # Revive state
        self.revive_idx = 0

        # Give to NPC state
        self.give_npc_idx = 0
        self.give_npc_item = None

        # Home state
        self.home_idx = 0
        self.home_sub = "menu"
        self.home_wh_side = 0
        self.home_wh_idx = 0
        self.home_train_idx = 0

        # NPC command selection (unique NPCs)
        self.npc_cmd_idx = 0
        self._npc_cmd_queue = []
        self._round_msgs = []
        self.current_npc_actor = None

        # Grave recovery state
        self.grave = None
        self.is_grave_battle = False

        # Ending / skill use
        self.game_cleared = False
        self.dungeon_skill_idx = 0

        # Title / job select
        self.title_idx = 0
        self.job_select_idx = 0
        self.unlocked_jobs = ["warrior"]

        # Dungeon merchant shop
        self.merchant_shop_idx = 0
        self._merchant_pos = None

        # Visual flash on item loss
        self.flash_timer = 0
        self.lost_item_name = ""

        # Screen shake
        self.shake_timer = 0

        # BGM zone tracking (-1 = none)
        self._current_bgm = -1

        # Per-message colors for _show_msgs
        self.msg_colors = []

        # UI Windows
        self.town_win = Window(8,  30, 240, 100, title="- DELVOKER -")
        self.status_win = Window(8, 143, 240,  72)
        self.sub_win = Window(10, 62, 236, 120)
        self.battle_win = Window(2, 150, SCREEN_W - 4, 88)
        self.inv_win = Window(8,  10, 240, 230, title="- INVENTORY -")
        self.inv_action_win = Window(78, 96, 100,  56, title="Action")
        self.shop_win = Window(8,  10, 240, 230, title="- SHOP -")

        self.state = None
        self._init_audio()
        self._set_state(STATE_TITLE)

        pyxel.run(self.update, self.draw)

    # ---- helpers ----

    def add_popup(self, text, x, y, color):
        self.popups.append({"text": text, "x": x, "y": y,
                           "color": color, "timer": 20})

    def _init_audio(self):
        # SE 0: attack (noise burst)
        pyxel.sounds[0].set("c3", "n", "7", "f", 5)
        # SE 1: hit impact (low noise thud)
        pyxel.sounds[1].set("c1", "n", "6", "f", 8)
        # SE 2: heal arpeggio (rising triangle)
        pyxel.sounds[2].set("c2e2g2c3", "t", "5555", "nnnn", 8)
        # BGM 3: Town (calm square wave melody)
        pyxel.sounds[3].set("e3g3a3g3e3c3d3e3", "s", "5", "n", 18)
        # BGM 4: Dungeon (ominous triangle drone)
        pyxel.sounds[4].set("c2c2a1a1g1g1a1a1", "t", "4", "n", 22)
        # BGM 5: Battle (upbeat pulse)
        pyxel.sounds[5].set("c3e3g3b3c4b3g3e3", "p", "6", "n", 12)
        pyxel.musics[0].set([3], [], [], [])
        pyxel.musics[1].set([4], [], [], [])
        pyxel.musics[2].set([5], [], [], [])

    # ---- state transitions ----

    def _set_state(self, new_state):
        self.state = new_state
        if new_state in (STATE_TITLE, STATE_JOB_SELECT):
            self.town_win.close()
            self.status_win.close()
            self.sub_win.close()
            self.battle_win.close()
            self.inv_win.close()
            self.inv_action_win.close()
            self.shop_win.close()
        elif new_state == STATE_TOWN:
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
            self.sub_win.close()
            self.inv_action_win.open()
        elif new_state == STATE_INV_GIVE_NPC:
            self.inv_action_win.close()
            self.sub_win.open()
        elif new_state == STATE_REVIVE:
            self.town_win.close()
            self.status_win.close()
            self.battle_win.close()
            self.inv_win.close()
            self.inv_action_win.close()
            self.shop_win.close()
            self.sub_win.open()
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
        elif new_state == STATE_HOME:
            self.town_win.close()
            self.status_win.close()
            self.battle_win.close()
            self.inv_win.close()
            self.inv_action_win.close()
            self.shop_win.close()
            self.sub_win.title = "HOME"
            self.sub_win.open()
        elif new_state == STATE_DUNGEON_SKILL:
            self.sub_win.title = "SKILLS"
            self.sub_win.open()
        elif new_state == STATE_DUNGEON_SHOP:
            self.town_win.close()
            self.status_win.close()
            self.sub_win.close()
            self.battle_win.close()
            self.inv_win.close()
            self.inv_action_win.close()
            self.shop_win.close()
        elif new_state == STATE_ENDING:
            self.town_win.close()
            self.status_win.close()
            self.sub_win.close()
            self.battle_win.close()
            self.inv_win.close()
            self.inv_action_win.close()
            self.shop_win.close()

        new_bgm = _BGM_ZONES.get(new_state, 0)
        if new_bgm != self._current_bgm:
            self._current_bgm = new_bgm
            if new_bgm == -1:
                pyxel.stop(3)
            else:
                pyxel.playm(new_bgm, loop=True)

    def wall_at(self, fwd, side):
        dx, dy = DIR_VECTORS[self.dir]
        rx, ry = DIR_VECTORS[(self.dir + 1) % 4]
        return is_wall(self.px + dx * fwd + rx * side,
                       self.py + dy * fwd + ry * side)

    # ---- Dungeon entry / floor management ----

    def _enter_dungeon_fresh(self):
        global _dungeon_map
        _dungeon_map = Map.generate_random(grave=self.grave, current_floor=1)
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
        if self.dungeon_floor >= 5 and "thief" not in self.unlocked_jobs:
            self.unlocked_jobs.append("thief")
        _dungeon_map = Map.generate_random(grave=self.grave, current_floor=self.dungeon_floor)
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
        npc_pool = _encounter_pool(self.dungeon_floor)
        count = random.randint(2, 4)
        positions = random.sample(floor_tiles, min(count, len(floor_tiles)))
        self.npcs = [NPC(random.choice(npc_pool), px, py)
                     for px, py in positions]

    def _interact_locked_door(self, nx, ny):
        key_item = next((it for it in self.player.inventory
                         if it.name == "Dungeon Key"), None)
        if key_item:
            self.player.inventory.remove(key_item)
            _dungeon_map.set_tile(nx, ny, TILE_FLOOR)
            lines = ["Used Dungeon Key.", "The door opens!"]
        else:
            lines = ["It's locked.", "Need a Dungeon Key."]
        self.sub_win.title = "DOOR"
        self.town_sub_lines = lines
        self._dialog_return_state = STATE_DUNGEON
        self._set_state(STATE_TOWN_SUB)

    def _interact_fountain(self, nx, ny):
        _dungeon_map.set_tile(nx, ny, TILE_FLOOR)
        roll = random.random()
        if roll < 0.70:
            restore_hp = max(1, self.player.max_hp * 30 // 100)
            restore_mp = max(1, self.player.max_mp * 30 // 100) if self.player.max_mp > 0 else 0
            self.player.hp = min(self.player.max_hp, self.player.hp + restore_hp)
            self.player.mp = min(self.player.max_mp, self.player.mp + restore_mp)
            lines = ["Blessed water restores your strength.",
                     f"+{restore_hp} HP  +{restore_mp} MP"]
        elif roll < 0.90:
            lines = ["The fountain is dry..."]
        else:
            self.player.status_effects["poison"] = 3
            lines = ["The water was tainted!", "You are poisoned."]
        self.sub_win.title = "FOUNTAIN"
        self.town_sub_lines = lines
        self._dialog_return_state = STATE_DUNGEON
        self._set_state(STATE_TOWN_SUB)

    def _interact_merchant(self, nx, ny):
        self._merchant_pos = (nx, ny)
        self.merchant_shop_idx = 0
        self._set_state(STATE_DUNGEON_SHOP)

    def _open_chest(self):
        global _dungeon_map
        _dungeon_map.set_tile(self.px, self.py, TILE_FLOOR)
        if len(self.player.inventory) >= INV_MAX:
            lines = ["A chest! Bag is full.", "Item was left behind..."]
        elif _dungeon_map.key_chest_pos == (self.px, self.py):
            item = ITEM_CATALOG["dungeon_key"].clone()
            self.player.inventory.append(item)
            _dungeon_map.key_chest_pos = None
            lines = ["Found a chest!", "Got: Dungeon Key!"]
        else:
            wp, ip = _drop_pools(self.dungeon_floor)
            if random.random() < 0.6:
                drop_key = random.choice(wp)
                base = ITEM_CATALOG[drop_key]
                item = make_enchanted_weapon(drop_key) if base.kind == "weapon" else (
                    make_enchanted_armor(drop_key) if base.kind == "armor" else base.clone())
            else:
                drop_key = random.choice(ip)
                base = ITEM_CATALOG[drop_key]
                item = make_enchanted_armor(
                    drop_key) if base.kind == "armor" else base.clone()
            self.player.inventory.append(item)
            name = item.label() if hasattr(item, "label") else item.name
            lines = ["Found a chest!", f"Got: {name}!"]
        self.sub_win.title = "CHEST"
        self.town_sub_lines = lines
        self._dialog_return_state = STATE_DUNGEON
        self._set_state(STATE_TOWN_SUB)

    # ---- Title / Job select ----

    def _upd_title(self):
        has_save = Path(SAVE_FILE).exists()
        options = ["New Game", "Continue"] if has_save else ["New Game"]
        if pyxel.btnp(pyxel.KEY_UP):
            self.title_idx = (self.title_idx - 1) % len(options)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.title_idx = (self.title_idx + 1) % len(options)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            sel = options[self.title_idx]
            self.player = Player()
            if sel == "Continue":
                self.load_data()
            else:
                self.unlocked_jobs = ["warrior"]
                self.game_cleared = False
            self.job_select_idx = 0
            self._set_state(STATE_JOB_SELECT)

    def _upd_job_select(self):
        jobs = self.unlocked_jobs
        if pyxel.btnp(pyxel.KEY_UP):
            self.job_select_idx = (self.job_select_idx - 1) % len(jobs)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.job_select_idx = (self.job_select_idx + 1) % len(jobs)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            job_key = jobs[self.job_select_idx]
            gold = self.player.gold
            warehouse = self.player.warehouse
            warehouse_max = self.player.warehouse_max
            perm_stats = dict(self.player.perm_stats)
            self.player = Player(job_key)
            self.player.gold = gold
            self.player.warehouse = warehouse
            self.player.warehouse_max = warehouse_max
            self.player.perm_stats = perm_stats
            self.party = Party(self.player)
            demo_npc = NPCMember("warrior", "Gard", "reckless")
            self.party.add(demo_npc)
            self._set_state(STATE_TOWN)

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
            elif sel == "Revive":
                self.revive_idx = 0
                self._set_state(STATE_REVIVE)
            elif sel == "Home":
                self.home_idx = 0
                self.home_sub = "menu"
                self._set_state(STATE_HOME)
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
            self.stat_alloc_idx = (
                self.stat_alloc_idx - 1) % len(STAT_ALLOC_NAMES)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.stat_alloc_idx = (
                self.stat_alloc_idx + 1) % len(STAT_ALLOC_NAMES)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            p = self.player
            if p.bonus_points > 0:
                attr = STAT_ALLOC_ATTRS[self.stat_alloc_idx]
                setattr(p, attr, getattr(p, attr) + 1)
                p.bonus_points -= 1

    # ---- Revive logic ----

    def _upd_revive(self):
        fallen = self.party.fallen
        if not fallen:
            if (pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE)
                    or pyxel.btnp(pyxel.KEY_X)):
                self._set_state(STATE_TOWN)
            return
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_TOWN)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.revive_idx = (self.revive_idx - 1) % len(fallen)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.revive_idx = (self.revive_idx + 1) % len(fallen)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            target = fallen[self.revive_idx]
            cost = target.level * 100
            if self.player.gold >= cost:
                self.player.gold -= cost
                target.hp = target.max_hp
                target.mp = target.max_mp
                self.revive_idx = 0

    # ---- Battle logic ----

    def _start_battle(self, enemy_key=None):
        key = enemy_key if enemy_key else random.choice(
            _encounter_pool(self.dungeon_floor))
        self.enemy = Enemy(ENEMY_CATALOG[key])
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
        edef = ENEMY_CATALOG.get(
            self._current_enemy_key) if self._current_enemy_key else None
        ai_type = edef.ai_type if edef else "normal"
        if ai_type == "ranged":
            return max(alive, key=lambda m: m.agi)
        if ai_type == "support":
            return min(alive, key=lambda m: m.hp)
        return alive[0]  # normal: attack first (player)

    def _npc_combat_action(self, npc, msgs):
        p = npc.personality

        if p == "reckless":
            attack_skills = [s for s in npc.skills
                             if s.effect_type == "attack" and npc.mp >= s.mp_cost]
            if attack_skills and random.random() < 0.40:
                skill = random.choice(attack_skills)
                npc.mp -= skill.mp_cost
                dmg = max(1, skill.power + npc.mag)
                self.enemy.hp = max(0, self.enemy.hp - dmg)
                msgs.append(
                    f"[Skill] {npc.name} uses {skill.name}! {self.enemy.name}: -{dmg} HP!")
            else:
                dmg = self._calc_dmg(npc.weapon, self.enemy.def_, self.enemy)
                self.enemy.hp = max(0, self.enemy.hp - dmg)
                msgs.append(
                    f"[Reckless] {npc.name} attacks! {self.enemy.name}: -{dmg} HP!")

        elif p == "cowardly":
            hurt = [m for m in self.party.alive if m.hp < m.max_hp * 0.5]
            heal_skills = [s for s in npc.skills
                           if s.effect_type == "heal" and npc.mp >= s.mp_cost]
            if hurt and heal_skills and random.random() < 0.80:
                skill = random.choice(heal_skills)
                target = min(hurt, key=lambda m: m.hp)
                npc.mp -= skill.mp_cost
                heal = skill.power
                target.hp = min(target.max_hp, target.hp + heal)
                msgs.append(
                    f"[Skill] {npc.name} uses {skill.name}! {target.name}: +{heal} HP!")
            else:
                msgs.append(
                    f"[Cowardly] {npc.name} hesitates and does nothing!")

        else:  # normal / selfish
            affordable = [s for s in npc.skills if npc.mp >= s.mp_cost]
            if affordable and random.random() < 0.20:
                skill = random.choice(affordable)
                npc.mp -= skill.mp_cost
                if skill.effect_type == "attack":
                    dmg = max(1, skill.power + npc.mag)
                    self.enemy.hp = max(0, self.enemy.hp - dmg)
                    msgs.append(
                        f"[Skill] {npc.name} uses {skill.name}! {self.enemy.name}: -{dmg} HP!")
                else:
                    alive = self.party.alive
                    if alive:
                        target = min(alive, key=lambda m: m.hp)
                        heal = skill.power
                        target.hp = min(target.max_hp, target.hp + heal)
                        msgs.append(
                            f"[Skill] {npc.name} uses {skill.name}! {target.name}: +{heal} HP!")
            else:
                dmg = self._calc_dmg(npc.weapon, self.enemy.def_, self.enemy)
                self.enemy.hp = max(0, self.enemy.hp - dmg)
                msgs.append(f"{npc.name} attacks! {self.enemy.name}: -{dmg} HP!")

    def _handle_victory(self, msgs):
        exp = self.enemy.exp_reward
        gold = self.enemy.gold_reward
        self.player.gold += gold
        level_ups = self.player.gain_exp(exp)
        self.level_up_gains = level_ups
        msgs.append(f"+{exp} EXP  +{gold} Gold")
        if level_ups:
            msgs.append(
                f"Level Up! Lv{self.player.level - len(level_ups)} -> Lv{self.player.level}")
            msgs.append(
                f"+3 Bonus Points! (Total: {self.player.bonus_points})")
            for lu in level_ups:
                parts = [f"HP+{lu['hp']}"]
                if lu["mp"] > 0:
                    parts.append(f"MP+{lu['mp']}")
                if lu["str"] > 0:
                    parts.append("STR+1")
                if lu["def"] > 0:
                    parts.append("DEF+1")
                if lu["agi"] > 0:
                    parts.append("AGI+1")
                msgs.append("  ".join(parts))
        if random.random() < DROP_RATE:
            wp, ip = _drop_pools(self.dungeon_floor)
            if random.random() < 0.6:
                drop_key = random.choice(wp)
                base_item = ITEM_CATALOG[drop_key]
                if base_item.kind == "weapon":
                    drop_item = make_enchanted_weapon(drop_key)
                elif base_item.kind == "armor":
                    drop_item = make_enchanted_armor(drop_key)
                else:
                    drop_item = base_item.clone()
            else:
                drop_key = random.choice(ip)
                base_item = ITEM_CATALOG[drop_key]
                if base_item.kind == "armor":
                    drop_item = make_enchanted_armor(drop_key)
                else:
                    drop_item = base_item.clone()
            if len(self.player.inventory) < INV_MAX:
                self.player.inventory.append(drop_item)
                msgs.append(
                    f"Got: {drop_item.label() if hasattr(drop_item, 'label') else drop_item.name}!")
            else:
                msgs.append("Bag full! Item lost.")
        if self.enemy and self._current_enemy_key:
            edef = ENEMY_CATALOG.get(self._current_enemy_key)
            if edef:
                for p in edef.parts:
                    if p["name"] in self.enemy.broken_parts and random.random() < 0.2:
                        drop_key = p.get("drop_flag")
                        if drop_key and drop_key in ITEM_CATALOG:
                            drop_item = ITEM_CATALOG[drop_key].clone()
                            if len(self.player.inventory) < INV_MAX:
                                self.player.inventory.append(drop_item)
                                msgs.append(
                                    f"[Part Drop] Got: {drop_item.name}!")
                            else:
                                msgs.append(
                                    f"[Part Drop] Bag full! {drop_item.name} lost.")

        if self.is_grave_battle and self.grave:
            recovered = self.grave.item
            rec_name = recovered.label() if hasattr(recovered, "label") else recovered.name
            self.player.inventory.append(recovered)
            msgs.append(f"Recovered: {rec_name}!")
            if _dungeon_map:
                _dungeon_map.set_tile(self.grave.x, self.grave.y, TILE_FLOOR)
            self.grave = None
            self.is_grave_battle = False

        self.battle_won = True
        if self._current_enemy_key == "dungeon_master":
            msgs.append("The Dungeon Master is defeated!")
            msgs.append("A path to the deeper floors opens...")
            self._next_floor()
            self._show_msgs(msgs, STATE_BATTLE_END)
        elif self._current_enemy_key == "archdemon":
            msgs.append("The Archdemon is defeated!")
            msgs.append("You have conquered the dungeon!")
            self.game_cleared = True
            if "mage" not in self.unlocked_jobs:
                self.unlocked_jobs.append("mage")
            self.save_data()
            self._show_msgs(msgs, STATE_ENDING)
        else:
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

    def _player_attack(self, part_name=None):
        pyxel.play(0, 0)
        dmg = self._calc_dmg(self.player.weapon, self.enemy.def_, self.enemy)
        dmg = max(1, dmg + self.player.perm_stats["str"])
        self.enemy.hp = max(0, self.enemy.hp - dmg)
        pyxel.play(1, 1)

        attr = getattr(self.player.weapon, "attribute", None)
        popup_col = COL_YELLOW if (
            attr and attr in self.enemy.weaknesses) else COL_WHITE
        self.add_popup(f"-{dmg}", 116, 68, popup_col)

        msgs = [f"{self.enemy.name}: -{dmg} HP!"]

        if part_name and part_name in self.enemy.part_hps and part_name not in self.enemy.broken_parts:
            self.enemy.part_hps[part_name] = max(
                0, self.enemy.part_hps[part_name] - dmg)
            if self.enemy.part_hps[part_name] <= 0:
                self.enemy.broken_parts.add(part_name)
                msgs.append(f"[PART BROKEN: {part_name}]")

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
            return None
        lost = random.choice(losable)
        if lost in p.inventory:
            p.inventory.remove(lost)
        elif lost is p.weapon:
            p.weapon = ITEM_CATALOG["old_dagger"]
        elif lost is p.armor:
            p.armor = None
        return lost

    def _enemy_turn(self, msgs=None):
        if msgs is None:
            msgs = []
        edef = ENEMY_CATALOG.get(
            self._current_enemy_key) if self._current_enemy_key else None

        # Boss telegraph: show warning turn before power attack
        if edef and edef.telegraph_message and not self.enemy_telegraphing and random.random() < 0.3:
            self.enemy_telegraphing = True
            msgs.append(edef.telegraph_message)
            self._show_msgs(msgs, STATE_BATTLE_CMD)
            return

        power_mult = 2 if self.enemy_telegraphing else 1
        self.enemy_telegraphing = False

        pyxel.play(0, 0)
        target = self._get_enemy_target()
        base_dmg = self._calc_dmg(self.enemy.weapon, target.total_def, target)
        dmg = int(base_dmg * power_mult)
        target.hp = max(0, target.hp - dmg)
        pyxel.play(1, 1)
        if power_mult > 1:
            msgs.append(f"[POWER] {target.name}: -{dmg} HP!")
        else:
            msgs.append(f"{target.name}: -{dmg} HP!")

        # Popup for incoming damage and screen shake
        self.add_popup(f"-{dmg}", 46, 126, COL_RED)
        self.shake_timer = 5

        # Status infliction
        if edef and edef.inflict_status and random.random() < edef.inflict_chance:
            inf = edef.inflict_status
            target.status_effects[inf] = max(
                target.status_effects.get(inf, 0), 3)
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
            lost_item = self._calc_item_loss()
            if lost_item:
                self.lost_item_name = lost_item.label() if hasattr(lost_item, "label") else lost_item.name
                msgs.append(f"ITEM LOST: {self.lost_item_name}...")
                self.grave = Grave(self.dungeon_floor, self.px, self.py, lost_item)
            else:
                self.lost_item_name = ""
            self.flash_timer = 20
            self._show_msgs(msgs, STATE_BATTLE_END)
        else:
            self._show_msgs(msgs, STATE_BATTLE_CMD)

    def _build_part_targets(self):
        targets = ["Body"]
        if self.enemy:
            for p in self.enemy.parts:
                if p["name"] not in self.enemy.broken_parts:
                    targets.append(p["name"])
        return targets

    def _upd_battle_target_part(self):
        targets = self._part_targets
        if pyxel.btnp(pyxel.KEY_X):
            self.state = STATE_BATTLE_CMD
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.part_idx = (self.part_idx - 1) % len(targets)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.part_idx = (self.part_idx + 1) % len(targets)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            sel = targets[self.part_idx]
            part_name = None if sel == "Body" else sel
            self.state = STATE_BATTLE_CMD
            self._player_attack(part_name)

    def _try_flee(self):
        if self._current_enemy_key in ("dungeon_master", "archdemon"):
            self._enemy_turn(["You cannot escape!"])
            return
        if random.random() < FLEE_RATE:
            self._show_msgs(["Got away safely!"], STATE_DUNGEON)
        else:
            self._enemy_turn(["Couldn't escape!"])

    @staticmethod
    def _msg_color(msg):
        if msg.startswith("Got:") or msg.startswith("Recovered:") or "[Part Drop]" in msg:
            return COL_YELLOW
        if "LOST" in msg or "Bag full" in msg:
            return COL_RED
        if "LEVEL UP" in msg or "HP+" in msg:
            return COL_GREEN
        if "[POWER]" in msg or "[Poison]" in msg:
            return COL_ORANGE
        if "defeated!" in msg or "conquered" in msg or "opens..." in msg:
            return COL_PEACH
        return COL_WHITE

    def _show_msgs(self, messages, next_state, colors=None):
        self.messages = messages
        self.msg_colors = colors or []
        self.msg_idx = 0
        self.next_state = next_state
        self.state = STATE_BATTLE_MSG

    # ---- Update ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.shake_timer > 0:
            self.shake_timer -= 1

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

        if self.state == STATE_TITLE:
            self._upd_title()
        elif self.state == STATE_JOB_SELECT:
            self._upd_job_select()
        elif self.state == STATE_TOWN:
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
        elif self.state == STATE_BATTLE_TARGET_PART:
            self._upd_battle_target_part()
        elif self.state == STATE_REVIVE:
            self._upd_revive()
        elif self.state == STATE_INV_GIVE_NPC:
            self._upd_inv_give_npc()
        elif self.state == STATE_HOME:
            self._upd_home()
        elif self.state == STATE_DUNGEON_SKILL:
            self._upd_dungeon_skill()
        elif self.state == STATE_DUNGEON_SHOP:
            self._upd_dungeon_shop()
        elif self.state == STATE_ENDING:
            self._upd_ending()

    def _upd_dungeon(self):
        global _dungeon_map
        if pyxel.btnp(pyxel.KEY_T):
            self.save_data()
            self._set_state(STATE_TOWN)
            return
        if pyxel.btnp(pyxel.KEY_I):
            self.pre_inv_state = STATE_DUNGEON
            self.inv_idx = 0
            self._set_state(STATE_INVENTORY)
            return
        if pyxel.btnp(pyxel.KEY_S):
            self.dungeon_skill_idx = 0
            self._set_state(STATE_DUNGEON_SKILL)
            return
        dx, dy = DIR_VECTORS[self.dir]
        moved = False
        if pyxel.btnp(pyxel.KEY_UP):
            nx, ny = self.px + dx, self.py + dy
            if _dungeon_map and _dungeon_map.tile_at(nx, ny) == TILE_LOCKED_DOOR:
                self._interact_locked_door(nx, ny)
                return
            elif _dungeon_map and _dungeon_map.tile_at(nx, ny) == TILE_FOUNTAIN:
                self._interact_fountain(nx, ny)
                return
            elif _dungeon_map and _dungeon_map.tile_at(nx, ny) == TILE_MERCHANT:
                self._interact_merchant(nx, ny)
                return
            elif not is_wall(nx, ny):
                self.px, self.py = nx, ny
                moved = True
        if pyxel.btnp(pyxel.KEY_DOWN):
            nx, ny = self.px - dx, self.py - dy
            if _dungeon_map and _dungeon_map.tile_at(nx, ny) == TILE_LOCKED_DOOR:
                self._interact_locked_door(nx, ny)
                return
            elif _dungeon_map and _dungeon_map.tile_at(nx, ny) == TILE_FOUNTAIN:
                self._interact_fountain(nx, ny)
                return
            elif _dungeon_map and _dungeon_map.tile_at(nx, ny) == TILE_MERCHANT:
                self._interact_merchant(nx, ny)
                return
            elif not is_wall(nx, ny):
                self.px, self.py = nx, ny
                moved = True
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.dir = (self.dir - 1) % 4
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.dir = (self.dir + 1) % 4
        if moved:
            if _dungeon_map is not None:
                _dungeon_map.visit(self.px, self.py)
            tile = _dungeon_map.tile_at(
                self.px, self.py) if _dungeon_map else 0
            if tile == TILE_STAIRS:
                if self.dungeon_floor == 5:
                    self._start_battle("dungeon_master")
                    self._show_msgs(
                        ["B5F - Midpoint of darkness.",
                         "The Dungeon Master emerges!"],
                        STATE_BATTLE_CMD
                    )
                elif self.dungeon_floor >= MAX_FLOOR:
                    self._start_battle("archdemon")
                    self._show_msgs(
                        [f"B{self.dungeon_floor}F - The deepest floor.",
                         "The Archdemon rises from the abyss!"],
                        STATE_BATTLE_CMD
                    )
                else:
                    self._next_floor()
                return
            if tile == TILE_CHEST:
                if random.random() < 0.2:
                    _dungeon_map.set_tile(self.px, self.py, TILE_FLOOR)
                    self._start_battle("mimic")
                    self._show_msgs(["The chest opens... It's a Mimic!"], STATE_BATTLE_CMD)
                else:
                    self._open_chest()
                return
            if tile == TILE_TRAP_SPIKE:
                dmg = random.randint(5, 10)
                self.player.hp = max(0, self.player.hp - dmg)
                _dungeon_map.set_tile(self.px, self.py, TILE_FLOOR)
                self.sub_win.title = "TRAP"
                self.town_sub_lines = ["Ouch! A spike trap!", f"You took {dmg} damage!"]
                self._dialog_return_state = STATE_DUNGEON
                self._set_state(STATE_TOWN_SUB)
                return
            if tile == TILE_TRAP_POISON:
                self.player.status_effects["poison"] = 3
                _dungeon_map.set_tile(self.px, self.py, TILE_FLOOR)
                self.sub_win.title = "TRAP"
                self.town_sub_lines = ["Poison needles! You are poisoned."]
                self._dialog_return_state = STATE_DUNGEON
                self._set_state(STATE_TOWN_SUB)
                return
            if tile == TILE_GRAVE:
                self.is_grave_battle = True
                self._start_battle("revenant")
                self._show_msgs(
                    ["You found your previous remains.",
                     "A vengeful spirit appears!"],
                    STATE_BATTLE_CMD
                )
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
                self._round_msgs.append(
                    f"{npc.name} attacks! {self.enemy.name}: -{dmg} HP!")
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
        npc_members = [m for m in self.party.members[1:]
                       if isinstance(m, NPCMember)]
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
                targets = self._build_part_targets()
                if len(targets) > 1:
                    self._part_targets = targets
                    self.part_idx = 0
                    self.state = STATE_BATTLE_TARGET_PART
                else:
                    self._player_attack()
            else:
                self._try_flee()

    def _upd_battle_msg(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self.msg_idx += 1
            if self.msg_idx >= len(self.messages):
                ns = self.next_state
                if ns in (STATE_DUNGEON, STATE_TOWN, STATE_ENDING):
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
                self.save_data()
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
            npc_members = [m for m in self.party.members[1:]
                           if isinstance(m, NPCMember)]
            if usable:
                self.inv_actions = ["Use", "Drop", "Cancel"]
            elif item.kind in ("weapon", "armor") and npc_members:
                self.inv_actions = ["Equip", "Give to NPC", "Drop", "Cancel"]
            else:
                self.inv_actions = ["Equip", "Drop", "Cancel"]
            self.inv_action_idx = 0
            self._set_state(STATE_INV_ACTION)

    def _upd_inv_action(self):
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_INVENTORY)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.inv_action_idx = (
                self.inv_action_idx - 1) % len(self.inv_actions)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.inv_action_idx = (
                self.inv_action_idx + 1) % len(self.inv_actions)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            sel = self.inv_actions[self.inv_action_idx]
            item = self.player.inventory[self.inv_idx]
            if sel == "Equip":
                self._do_equip(item)
            elif sel == "Use":
                if self._do_use(item):
                    return
            elif sel == "Drop":
                self.player.inventory.remove(item)
                self.inv_idx = min(self.inv_idx, max(
                    0, len(self.player.inventory) - 1))
            elif sel == "Give to NPC":
                self.give_npc_item = item
                self.give_npc_idx = 0
                self._set_state(STATE_INV_GIVE_NPC)
                return
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

    def _upd_inv_give_npc(self):
        npc_members = [m for m in self.party.members[1:]
                       if isinstance(m, NPCMember)]
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_INV_ACTION)
            return
        if not npc_members:
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                self._set_state(STATE_INV_ACTION)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.give_npc_idx = (self.give_npc_idx - 1) % len(npc_members)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.give_npc_idx = (self.give_npc_idx + 1) % len(npc_members)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            item = self.give_npc_item
            npc = npc_members[self.give_npc_idx]
            p = self.player
            if item.kind == "weapon":
                old_item = npc.weapon
                p.inventory.remove(item)
                npc.weapon = item
                if old_item:
                    p.inventory.append(old_item)
            elif item.kind == "armor":
                old_item = npc.armor
                p.inventory.remove(item)
                npc.armor = item
                if old_item:
                    p.inventory.append(old_item)
            self.inv_idx = min(self.inv_idx, max(0, len(p.inventory) - 1))
            self.give_npc_item = None
            self._set_state(STATE_INVENTORY)

    def _do_use(self, item):
        p = self.player
        if item.name == "Scroll: Mapping":
            if _dungeon_map:
                for vy in range(_dungeon_map.height):
                    for vx in range(_dungeon_map.width):
                        if _dungeon_map.tiles[vy][vx] != TILE_WALL:
                            _dungeon_map.visited[vy][vx] = True
            p.inventory.remove(item)
            self.inv_idx = min(self.inv_idx, max(0, len(p.inventory) - 1))
            self.sub_win.title = "SCROLL"
            self.town_sub_lines = ["The entire floor map is revealed!"]
            self._dialog_return_state = self.pre_inv_state
            self._set_state(STATE_TOWN_SUB)
            return True
        if isinstance(item, GrimoireItem):
            new_skill = Skill(item.skill_name, item.mp_cost,
                              item.effect_type, item.power,
                              getattr(item, "is_utility", False))
            if len(p.skills) >= MAX_SKILLS:
                p.skills.pop(0)
            p.skills.append(new_skill)
        else:
            heal_hp = min(p.max_hp - p.hp, item.hp_restore)
            p.hp = min(p.max_hp, p.hp + item.hp_restore)
            p.mp = min(p.max_mp, p.mp + item.mp_restore)
            if heal_hp > 0:
                self.add_popup(f"+{heal_hp}", 46, 130, COL_GREEN)
                pyxel.play(2, 2)
            cure = getattr(item, "cure_status", "")
            if cure and cure in p.status_effects:
                p.status_effects[cure] = 0
                pyxel.play(2, 2)
        p.inventory.remove(item)
        self.inv_idx = min(self.inv_idx, max(0, len(p.inventory) - 1))
        return False

    # ---- Dungeon skill use ----

    def _upd_dungeon_skill(self):
        utility = [s for s in self.player.skills if s.effect_type == "teleport"]
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_DUNGEON)
            return
        if not utility:
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.dungeon_skill_idx = (self.dungeon_skill_idx - 1) % len(utility)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.dungeon_skill_idx = (self.dungeon_skill_idx + 1) % len(utility)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            skill = utility[self.dungeon_skill_idx]
            if self.player.mp >= skill.mp_cost:
                self.player.mp -= skill.mp_cost
                self.save_data()
                self._set_state(STATE_TOWN)

    # ---- Dungeon merchant shop ----

    def _upd_dungeon_shop(self):
        if pyxel.btnp(pyxel.KEY_X):
            if self._merchant_pos:
                _dungeon_map.set_tile(self._merchant_pos[0], self._merchant_pos[1], TILE_FLOOR)
                self._merchant_pos = None
            self._set_state(STATE_DUNGEON)
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.merchant_shop_idx = (self.merchant_shop_idx - 1) % len(MERCHANT_KEYS)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.merchant_shop_idx = (self.merchant_shop_idx + 1) % len(MERCHANT_KEYS)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            if len(self.player.inventory) >= INV_MAX:
                return
            key = MERCHANT_KEYS[self.merchant_shop_idx]
            item = ITEM_CATALOG[key]
            price = int(item.value * 1.5)
            if self.player.gold >= price:
                self.player.gold -= price
                self.player.inventory.append(item.clone())

    # ---- Ending ----

    def _upd_ending(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self.save_data()
            self._set_state(STATE_TOWN)

    # ---- Home logic ----

    def _upd_home(self):
        sub = self.home_sub
        p = self.player

        if sub == "menu":
            if pyxel.btnp(pyxel.KEY_X):
                self.sub_win.title = None
                self._set_state(STATE_TOWN)
                return
            if pyxel.btnp(pyxel.KEY_UP):
                self.home_idx = (self.home_idx - 1) % len(HOME_MENU)
            if pyxel.btnp(pyxel.KEY_DOWN):
                self.home_idx = (self.home_idx + 1) % len(HOME_MENU)
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                sel = HOME_MENU[self.home_idx]
                if sel == "Warehouse":
                    self.home_sub = "warehouse"
                    self.home_wh_side = 0
                    self.home_wh_idx = 0
                    self.sub_win.close()
                    self.inv_win.title = "HOME: WAREHOUSE"
                    self.inv_win.open()
                elif sel == "Renovate":
                    self.home_sub = "renovate"
                elif sel == "Training":
                    self.home_sub = "training"
                    self.home_train_idx = 0
                elif sel == "Back":
                    self.sub_win.title = None
                    self._set_state(STATE_TOWN)

        elif sub == "warehouse":
            bag = p.inventory
            storage = p.warehouse
            if pyxel.btnp(pyxel.KEY_X):
                self.home_sub = "menu"
                self.inv_win.title = "- INVENTORY -"
                self.inv_win.close()
                self.sub_win.open()
                return
            if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT):
                self.home_wh_side = 1 - self.home_wh_side
                self.home_wh_idx = 0
            current = bag if self.home_wh_side == 0 else storage
            if current:
                if pyxel.btnp(pyxel.KEY_UP):
                    self.home_wh_idx = (self.home_wh_idx - 1) % len(current)
                if pyxel.btnp(pyxel.KEY_DOWN):
                    self.home_wh_idx = (self.home_wh_idx + 1) % len(current)
                if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                    idx = min(self.home_wh_idx, len(current) - 1)
                    item = current[idx]
                    if self.home_wh_side == 0 and len(storage) < p.warehouse_max:
                        bag.remove(item)
                        storage.append(item)
                        self.home_wh_idx = min(self.home_wh_idx, max(0, len(bag) - 1))
                    elif self.home_wh_side == 1 and len(bag) < INV_MAX:
                        storage.remove(item)
                        bag.append(item)
                        self.home_wh_idx = min(self.home_wh_idx, max(0, len(storage) - 1))

        elif sub == "renovate":
            if pyxel.btnp(pyxel.KEY_X):
                self.home_sub = "menu"
                return
            current_level = (p.warehouse_max - 10) // HOME_RENOVATE_SLOTS
            if current_level < len(HOME_RENOVATE_COSTS):
                cost = HOME_RENOVATE_COSTS[current_level]
                if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                    if p.gold >= cost:
                        p.gold -= cost
                        p.warehouse_max += HOME_RENOVATE_SLOTS
            else:
                if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                    self.home_sub = "menu"

        elif sub == "training":
            if pyxel.btnp(pyxel.KEY_X):
                self.home_sub = "menu"
                return
            if pyxel.btnp(pyxel.KEY_UP):
                self.home_train_idx = (self.home_train_idx - 1) % len(HOME_TRAIN_STATS)
            if pyxel.btnp(pyxel.KEY_DOWN):
                self.home_train_idx = (self.home_train_idx + 1) % len(HOME_TRAIN_STATS)
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                attr = HOME_TRAIN_ATTRS[self.home_train_idx]
                current = p.perm_stats[attr]
                cost = (current + 1) * 1000
                if p.gold >= cost:
                    p.gold -= cost
                    p.perm_stats[attr] += 1
                    self.save_data()

    # ---- Persistence ----

    @staticmethod
    def _serialize_item(item):
        if isinstance(item, EnchantedWeapon):
            prefix = item.prefix
            return {"kind": "enchanted_weapon",
                    "base_name": item._base_name,
                    "base_dc": item.dice_count - (prefix["dice_count_mod"] if prefix else 0),
                    "base_ds": item.dice_sides - (prefix["dice_sides_mod"] if prefix else 0),
                    "base_sb": item.static_bonus - (prefix["static_bonus_mod"] if prefix else 0),
                    "enchant_bonus": item.enchant_bonus, "value": item.value,
                    "prefix": prefix, "suffix": item.suffix}
        if isinstance(item, WeaponItem):
            return {"kind": "weapon",
                    "name": item.name, "dice_count": item.dice_count,
                    "dice_sides": item.dice_sides, "static_bonus": item.static_bonus,
                    "enchant_bonus": item.enchant_bonus, "value": item.value,
                    "attribute": item.attribute}
        if isinstance(item, EnchantedArmor):
            prefix = item.prefix
            return {"kind": "enchanted_armor",
                    "base_name": item._base_name,
                    "base_def": item.def_bonus - (prefix["def_bonus_mod"] if prefix else 0),
                    "value": item.value, "prefix": prefix, "suffix": item.suffix}
        if isinstance(item, ArmorItem):
            return {"kind": "armor",
                    "name": item.name, "def_bonus": item.def_bonus, "value": item.value}
        if isinstance(item, GrimoireItem):
            return {"kind": "grimoire",
                    "name": item.name, "skill_name": item.skill_name,
                    "mp_cost": item.mp_cost, "effect_type": item.effect_type,
                    "power": item.power, "value": item.value, "is_utility": item.is_utility}
        return {"kind": "consumable",
                "name": item.name, "hp_restore": getattr(item, "hp_restore", 0),
                "mp_restore": getattr(item, "mp_restore", 0), "value": item.value,
                "cure_status": getattr(item, "cure_status", "")}

    @staticmethod
    def _deserialize_item(d):
        k = d.get("kind", "consumable")
        if k == "enchanted_weapon":
            base = WeaponItem(d["base_name"], d["base_dc"], d["base_ds"],
                              d.get("base_sb", 0), d.get("enchant_bonus", 0), d.get("value", 0))
            return EnchantedWeapon(base, d.get("prefix"), d.get("suffix"))
        if k == "weapon":
            return WeaponItem(d["name"], d["dice_count"], d["dice_sides"],
                              d.get("static_bonus", 0), d.get("enchant_bonus", 0),
                              d.get("value", 0), d.get("attribute"))
        if k == "enchanted_armor":
            base = ArmorItem(d["base_name"], d["base_def"], d.get("value", 0))
            return EnchantedArmor(base, d.get("prefix"), d.get("suffix"))
        if k == "armor":
            return ArmorItem(d["name"], d["def_bonus"], d.get("value", 0))
        if k == "grimoire":
            return GrimoireItem(d["name"], d["skill_name"], d.get("mp_cost", 5),
                                d.get("effect_type", "attack"), d.get("power", 10),
                                d.get("value", 0), d.get("is_utility", False))
        return ConsumableItem(d["name"], d.get("hp_restore", 0), d.get("mp_restore", 0),
                              d.get("value", 0), d.get("cure_status", ""))

    def save_data(self):
        data = {
            "gold": self.player.gold,
            "warehouse": [self._serialize_item(it) for it in self.player.warehouse],
            "warehouse_max": self.player.warehouse_max,
            "perm_stats": dict(self.player.perm_stats),
            "unlocked_jobs": list(self.unlocked_jobs),
            "game_cleared": self.game_cleared,
        }
        with open(SAVE_FILE, "w", encoding="ascii") as f:
            json.dump(data, f, ensure_ascii=True)

    def load_data(self):
        try:
            with open(SAVE_FILE, encoding="ascii") as f:
                data = json.load(f)
            self.player.gold = data.get("gold", 0)
            self.player.warehouse = [self._deserialize_item(d)
                                     for d in data.get("warehouse", [])]
            self.player.warehouse_max = data.get("warehouse_max", 10)
            self.player.perm_stats = data.get("perm_stats", {"str": 0, "def": 0, "mag": 0})
            self.unlocked_jobs = data.get("unlocked_jobs", ["warrior"])
            self.game_cleared = data.get("game_cleared", False)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

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
        if self.shake_timer > 0:
            pyxel.camera(random.randint(-2, 2), random.randint(-2, 2))
        pyxel.cls(COL_NAVY)
        if self.state == STATE_TITLE:
            self._draw_title()
        elif self.state == STATE_JOB_SELECT:
            self._draw_job_select()
        elif self.state == STATE_TOWN:
            self._draw_town()
        elif self.state == STATE_TOWN_SUB:
            self._draw_town_sub()
        elif self.state == STATE_DUNGEON:
            self.draw_3d_view()
            self.draw_npcs()
            self.draw_status()
            self.draw_minimap()
        elif self.state == STATE_DUNGEON_SKILL:
            self.draw_3d_view()
            self.draw_npcs()
            self.draw_status()
            self.draw_minimap()
            self._draw_dungeon_skill()
        elif self.state == STATE_DUNGEON_SHOP:
            self._draw_dungeon_shop()
        elif self.state == STATE_ENDING:
            self._draw_ending()
        elif self.state in (STATE_INVENTORY, STATE_INV_ACTION, STATE_INV_GIVE_NPC):
            self._draw_inventory()
        elif self.state == STATE_HOME:
            self._draw_home()
        elif self.state == STATE_REVIVE:
            self._draw_revive()
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
        if self.shake_timer > 0:
            pyxel.camera()

    def _draw_town(self):
        pyxel.cls(COL_BLACK)

        def _menu_content(cx, cy, cw, ch):
            sub = "Solace Town"
            pyxel.text(cx + (cw - len(sub) * 4) // 2, cy, sub, COL_WHITE)
            for i, item in enumerate(TOWN_MENU):
                col = COL_YELLOW if i == self.town_cmd_idx else COL_WHITE
                cursor = ">" if i == self.town_cmd_idx else " "
                pyxel.text(cx + 4, cy + 12 + i * 14, f"{cursor} {item}", col)

        self.town_win.draw(_menu_content)

        def _status_content(cx, cy, cw, ch):
            p = self.player
            pyxel.text(
                cx, cy,     f"{p.name}  Lv{p.level} {p.job.name}", COL_WHITE)
            pyxel.text(
                cx, cy+12,  f"HP: {p.hp}/{p.max_hp}   MP: {p.mp}/{p.max_mp}", COL_GREEN)
            pyxel.text(
                cx, cy+24,  f"EXP: {p.exp}/{p.exp_to_next}   Gold: {p.gold}", COL_YELLOW)
            pyxel.text(cx, cy+36,  f"Weapon: {p.weapon.label()}", COL_PEACH)
            if p.bonus_points > 0:
                pyxel.text(
                    cx, cy+48, f"Bonus Points: {p.bonus_points}  (Stats menu)", COL_ORANGE)

        self.status_win.draw(_status_content)
        pyxel.text(6, 240, "Z/Space:Enter  Up/Down:Select  Q:Quit",
                   COL_DARK_GRAY)

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
                pyxel.text(cx, cy + 28 + i * 14,
                           f"{cursor} {name}: {val}", col)
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
        pyxel.text(
            bx, by + 6, f"HP {self.enemy.hp}/{self.enemy.max_hp}", COL_LIGHT_GRAY)

        pyxel.line(0, 122, SCREEN_W - 1, 122, COL_DARK_GRAY)

        p = self.player
        p_hp_f = p.hp / p.max_hp
        pyxel.text(
            4, 126, f"{p.name} Lv{p.level} {p.job.name}  HP {p.hp}/{p.max_hp}", COL_WHITE)
        pyxel.rect(4, 136, 100, 4, COL_DARK_GRAY)
        p_col = COL_GREEN if p_hp_f > 0.4 else (
            COL_ORANGE if p_hp_f > 0.2 else COL_RED)
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
            npc_col = COL_GREEN if npc.hp > npc.max_hp * \
                0.4 else (COL_ORANGE if npc.hp > 0 else COL_RED)
            pyxel.text(4 + i * 128, 142,
                       f"{npc.name[:6]} HP:{npc.hp}/{npc.max_hp}", npc_col)
            npc_icon_x = 4 + i * 128 + 80
            if npc.status_effects.get("poison", 0) > 0:
                pyxel.text(npc_icon_x, 142, "[P]", COL_GREEN)
                npc_icon_x += 16
            if npc.status_effects.get("stun", 0) > 0:
                pyxel.text(npc_icon_x, 142, "[S]", COL_YELLOW)

        def _panel_content(cx, cy, cw, ch):
            if self.state == STATE_BATTLE_CMD:
                for i, cmd in enumerate(COMMANDS):
                    col = COL_YELLOW if i == self.cmd_idx else COL_WHITE
                    cursor = ">" if i == self.cmd_idx else " "
                    pyxel.text(cx, cy + i * 16, f"{cursor} {cmd}", col)
                pyxel.text(cx, cy + 40, p.weapon.label(), COL_PEACH)
                if p.skills:
                    skill_names = "  ".join(s.name[:8] for s in p.skills)
                    pyxel.text(
                        cx, cy + 52, f"Skills: {skill_names}", COL_INDIGO)
                pyxel.text(6, cy + ch - 8,
                           "Z/Space:OK  Up/Down:Select", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_NPC_CMD:
                npc = self.current_npc_actor
                tag = "[Unique]" if npc.is_unique else ""
                pyxel.text(cx, cy - 8, f"{npc.name} {tag}", COL_PEACH)
                for i, cmd in enumerate(COMMANDS):
                    col = COL_YELLOW if i == self.npc_cmd_idx else COL_WHITE
                    cursor = ">" if i == self.npc_cmd_idx else " "
                    pyxel.text(cx, cy + i * 16, f"{cursor} {cmd}", col)
                pyxel.text(cx, cy + 40, npc.weapon.label(), COL_PEACH)
                pyxel.text(6, cy + ch - 8,
                           "Z/Space:OK  Up/Down:Select", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_TARGET_PART:
                pyxel.text(cx, cy, "Target:", COL_YELLOW)
                for i, t in enumerate(self._part_targets):
                    col = COL_YELLOW if i == self.part_idx else COL_WHITE
                    cur = ">" if i == self.part_idx else " "
                    hp_info = ""
                    if t != "Body" and self.enemy and t in self.enemy.part_hps:
                        hp_info = f" HP:{self.enemy.part_hps[t]}"
                    pyxel.text(cx, cy + 12 + i * 14,
                               f"{cur} {t}{hp_info}", col)
                pyxel.text(6, cy + ch - 8,
                           "Z:OK  X:Cancel  Up/Down:Select", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_MSG:
                if self.msg_idx < len(self.messages):
                    txt = self.messages[self.msg_idx]
                    msg_col = (self.msg_colors[self.msg_idx]
                               if self.msg_idx < len(self.msg_colors)
                               else self._msg_color(txt))
                    pyxel.text(cx, cy + 20, txt, msg_col)
                pyxel.text(SCREEN_W - 58, cy + ch - 8, "Z:Next", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_END:
                if self.battle_won:
                    pyxel.text(cx + (cw - 32) // 2, cy +
                               8, "VICTORY!", COL_YELLOW)
                    bp = self.player
                    pyxel.text(
                        cx, cy + 22, f"HP:{bp.hp}/{bp.max_hp}  EXP:{bp.exp}/{bp.exp_to_next}", COL_GREEN)
                    if self.level_up_gains:
                        lu = self.level_up_gains[-1]
                        parts = [f"HP+{lu['hp']}"]
                        if lu["mp"] > 0:
                            parts.append(f"MP+{lu['mp']}")
                        if lu["str"] > 0:
                            parts.append("STR+1")
                        if lu["def"] > 0:
                            parts.append("DEF+1")
                        if lu["agi"] > 0:
                            parts.append("AGI+1")
                        pyxel.text(cx, cy + 34, "  ".join(parts), COL_PEACH)
                else:
                    pyxel.text(cx + (cw - 44) // 2, cy +
                               14, "DEFEATED...", COL_RED)
                    pyxel.text(cx + (cw - 80) // 2, cy + 28,
                               "Returning to town...", COL_DARK_GRAY)
                pyxel.text(SCREEN_W - 82, cy + ch - 8,
                           "Z:Continue", COL_DARK_GRAY)

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
                    eq = item is self.player.weapon or item is self.player.armor
                    tag = {"weapon": "W", "armor": "A",
                           "consumable": "C"}.get(item.kind, "?")
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
                    display = item.label() if hasattr(item, "label") else item.name
                    pyxel.text(cx,           cy + i * 14,
                               f"{cursor} {display}", name_col)
                    pyxel.text(cx + cw - 12, cy + i * 14,
                               f"[{tag}]", COL_LIGHT_GRAY)
            p = self.player
            pyxel.text(
                cx, cy + ch - 16, f"Gold: {p.gold}G   {len(p.inventory)}/{INV_MAX} items", COL_YELLOW)
            pyxel.text(
                cx, cy + ch - 8,  "Z:Select  X:Close  [W]eap [A]rmor [C]onsumable", COL_DARK_GRAY)

        self.inv_win.draw(_inv_content)

        if self.state == STATE_INV_ACTION:
            def _action_content(cx, cy, _cw, _ch):
                for i, act in enumerate(self.inv_actions):
                    col = COL_YELLOW if i == self.inv_action_idx else COL_WHITE
                    cur = ">" if i == self.inv_action_idx else " "
                    pyxel.text(cx, cy + i * 14, f"{cur} {act}", col)
            self.inv_action_win.draw(_action_content)

        if self.state == STATE_INV_GIVE_NPC:
            def _npc_sel_content(cx, cy, _cw, ch):
                pyxel.text(cx, cy, "== Give to NPC ==", COL_YELLOW)
                npc_members = [m for m in self.party.members[1:]
                               if isinstance(m, NPCMember)]
                if not npc_members:
                    pyxel.text(cx, cy + 16, "No NPC in party.", COL_DARK_GRAY)
                else:
                    for i, npc in enumerate(npc_members):
                        cursor = ">" if i == self.give_npc_idx else " "
                        col = COL_YELLOW if i == self.give_npc_idx else COL_WHITE
                        pyxel.text(cx, cy + 16 + i * 14,
                                   f"{cursor} {npc.name}", col)
                pyxel.text(cx, cy + ch - 8, "Z:Give  X:Cancel", COL_DARK_GRAY)
            self.sub_win.draw(_npc_sel_content)

    def _draw_dungeon_skill(self):
        def _content(cx, cy, cw, ch):
            p = self.player
            pyxel.text(cx, cy, "== DUNGEON SKILLS ==", COL_YELLOW)
            pyxel.text(cx, cy + 12, f"MP: {p.mp}/{p.max_mp}", COL_GREEN)
            utility = [s for s in p.skills if s.effect_type == "teleport"]
            if not utility:
                pyxel.text(cx, cy + 28, "No utility skills.", COL_DARK_GRAY)
            else:
                for i, sk in enumerate(utility):
                    cur = ">" if i == self.dungeon_skill_idx else " "
                    can_use = p.mp >= sk.mp_cost
                    col = COL_YELLOW if i == self.dungeon_skill_idx else (
                        COL_WHITE if can_use else COL_DARK_GRAY)
                    pyxel.text(cx, cy + 28 + i * 14,
                               f"{cur} {sk.name}  MP:{sk.mp_cost}", col)
            pyxel.text(cx, cy + ch - 8, "Z:Use  X:Cancel", COL_DARK_GRAY)
        self.sub_win.draw(_content)

    def _draw_dungeon_shop(self):
        self.draw_3d_view()
        self.draw_npcs()
        self.draw_status()
        self.draw_minimap()
        # Merchant panel overlays 3D view area (y=10 to y=170), status bar remains visible
        px, py, pw, ph = 8, 10, 240, 160
        pyxel.rect(px, py, pw, ph, COL_BLACK)
        pyxel.rectb(px, py, pw, ph, COL_WHITE)
        pyxel.text(px + 4, py + 4, "=WANDERING MERCHANT=", COL_YELLOW)
        for i, key in enumerate(MERCHANT_KEYS):
            item = ITEM_CATALOG[key]
            price = int(item.value * 1.5)
            col = COL_YELLOW if i == self.merchant_shop_idx else COL_WHITE
            cursor = ">" if i == self.merchant_shop_idx else " "
            affordable = self.player.gold >= price
            name_col = col if affordable else COL_DARK_GRAY
            pyxel.text(px + 4,       py + 18 + i * 14, f"{cursor} {item.name}", name_col)
            pyxel.text(px + pw - 40, py + 18 + i * 14, f"{price}G",
                       COL_YELLOW if affordable else COL_DARK_GRAY)
        p = self.player
        pyxel.text(px + 4, py + ph - 18, f"Gold: {p.gold}G", COL_YELLOW)
        if len(p.inventory) >= INV_MAX:
            pyxel.text(px + 64, py + ph - 18, "Bag Full!", COL_RED)
        pyxel.text(px + 4, py + ph - 8, "Z:Buy  X:Back", COL_DARK_GRAY)

    def _draw_title(self):
        pyxel.cls(COL_BLACK)
        title = "D E L V O K E R"
        pyxel.text((SCREEN_W - len(title) * 4) // 2, 55, title, COL_YELLOW)
        sub = "Retro Dungeon Hack & Slash"
        pyxel.text((SCREEN_W - len(sub) * 4) // 2, 70, sub, COL_LIGHT_GRAY)
        has_save = Path(SAVE_FILE).exists()
        options = ["New Game", "Continue"] if has_save else ["New Game"]
        for i, opt in enumerate(options):
            cur = ">" if i == self.title_idx else " "
            col = COL_YELLOW if i == self.title_idx else COL_WHITE
            x = (SCREEN_W - (len(opt) + 2) * 4) // 2
            pyxel.text(x, 108 + i * 16, f"{cur} {opt}", col)
        pyxel.text(4, SCREEN_H - 14, "Z/Space:Select  Q:Quit", COL_DARK_GRAY)

    def _draw_job_select(self):
        pyxel.cls(COL_BLACK)
        hdr = "SELECT YOUR JOB"
        pyxel.text((SCREEN_W - len(hdr) * 4) // 2, 30, hdr, COL_YELLOW)
        for i, job_key in enumerate(self.unlocked_jobs):
            job = JOBS[job_key]
            cur = ">" if i == self.job_select_idx else " "
            col = COL_YELLOW if i == self.job_select_idx else COL_WHITE
            pyxel.text(72, 60 + i * 24, f"{cur} {job.name}", col)
            start_hp = job.hp_die * 3
            start_mp = job.mp_die * 2 if job.mp_die > 0 else 0
            mp_str = f" MP:{start_mp}" if start_mp > 0 else ""
            pyxel.text(80, 70 + i * 24, f"HP:{start_hp}{mp_str}", COL_LIGHT_GRAY)
        pyxel.text(4, SCREEN_H - 14, "Z/Space:Select", COL_DARK_GRAY)

    def _draw_ending(self):
        pyxel.cls(COL_BLACK)
        p = self.player
        lines = [
            ("CONGRATULATIONS!", COL_YELLOW, 40),
            ("You conquered the Dungeon!", COL_WHITE, 60),
            ("The Archdemon is slain!", COL_GREEN, 76),
            ("", COL_WHITE, 92),
            (f"Name:  {p.name}", COL_WHITE, 100),
            (f"Level: {p.level}", COL_WHITE, 112),
            (f"Floor: B{self.dungeon_floor}F", COL_PEACH, 124),
            (f"Gold:  {p.gold}G", COL_YELLOW, 136),
        ]
        for text, col, y in lines:
            if text:
                x = (SCREEN_W - len(text) * 4) // 2
                pyxel.text(x, y, text, col)
        hint = "Z: Return to Town"
        pyxel.text((SCREEN_W - len(hint) * 4) // 2, 170, hint, COL_DARK_GRAY)

    def _draw_home(self):
        pyxel.cls(COL_BLACK)
        sub = self.home_sub
        p = self.player

        if sub == "menu":
            def _menu(cx, cy, cw, ch):
                pyxel.text(cx, cy, "Solace Town - Your Base", COL_WHITE)
                pyxel.text(cx, cy + 10,
                           f"Warehouse: {len(p.warehouse)}/{p.warehouse_max}  "
                           f"STR+{p.perm_stats['str']} DEF+{p.perm_stats['def']} MAG+{p.perm_stats['mag']}",
                           COL_LIGHT_GRAY)
                for i, label in enumerate(HOME_MENU):
                    col = COL_YELLOW if i == self.home_idx else COL_WHITE
                    cur = ">" if i == self.home_idx else " "
                    pyxel.text(cx, cy + 26 + i * 14, f"{cur} {label}", col)
                pyxel.text(cx, cy + ch - 8, "Z:Select  X:Back", COL_DARK_GRAY)
            self.sub_win.draw(_menu)

        elif sub == "warehouse":
            def _wh(cx, cy, cw, ch):
                bag = p.inventory
                storage = p.warehouse
                half = cw // 2 - 1
                bag_col = COL_YELLOW if self.home_wh_side == 0 else COL_LIGHT_GRAY
                sto_col = COL_YELLOW if self.home_wh_side == 1 else COL_LIGHT_GRAY
                pyxel.text(cx,          cy, f"BAG ({len(bag)}/{INV_MAX})", bag_col)
                pyxel.text(cx + half + 3, cy, f"STORAGE ({len(storage)}/{p.warehouse_max})", sto_col)
                pyxel.line(cx + half + 1, cy + 8, cx + half + 1, cy + ch - 14, COL_DARK_GRAY)
                max_rows = (ch - 22) // 10
                for i in range(max_rows):
                    if i < len(bag):
                        cur = ">" if (self.home_wh_side == 0 and i == self.home_wh_idx) else " "
                        col = COL_YELLOW if (self.home_wh_side == 0 and i == self.home_wh_idx) else COL_WHITE
                        name = bag[i].label() if hasattr(bag[i], "label") else bag[i].name
                        pyxel.text(cx, cy + 12 + i * 10, f"{cur}{name[:22]}", col)
                    if i < len(storage):
                        cur = ">" if (self.home_wh_side == 1 and i == self.home_wh_idx) else " "
                        col = COL_YELLOW if (self.home_wh_side == 1 and i == self.home_wh_idx) else COL_WHITE
                        name = storage[i].label() if hasattr(storage[i], "label") else storage[i].name
                        pyxel.text(cx + half + 3, cy + 12 + i * 10, f"{cur}{name[:22]}", col)
                pyxel.text(cx, cy + ch - 8, "Z:Transfer  L/R:Side  X:Back", COL_DARK_GRAY)
            self.inv_win.draw(_wh)

        elif sub == "renovate":
            def _ren(cx, cy, cw, ch):
                current_level = (p.warehouse_max - 10) // HOME_RENOVATE_SLOTS
                pyxel.text(cx, cy, "== RENOVATE ==", COL_YELLOW)
                pyxel.text(cx, cy + 14, f"Current slots: {p.warehouse_max}", COL_WHITE)
                if current_level >= len(HOME_RENOVATE_COSTS):
                    pyxel.text(cx, cy + 28, "Max level reached!", COL_GREEN)
                    pyxel.text(cx, cy + ch - 8, "Z/X:Back", COL_DARK_GRAY)
                else:
                    cost = HOME_RENOVATE_COSTS[current_level]
                    aff = p.gold >= cost
                    pyxel.text(cx, cy + 28, f"Next: +{HOME_RENOVATE_SLOTS} slots", COL_WHITE)
                    pyxel.text(cx, cy + 40, f"Cost: {cost}G",
                               COL_YELLOW if aff else COL_DARK_GRAY)
                    pyxel.text(cx, cy + 52, f"Gold: {p.gold}G", COL_YELLOW)
                    pyxel.text(cx, cy + ch - 8, "Z:Upgrade  X:Back", COL_DARK_GRAY)
            self.sub_win.draw(_ren)

        elif sub == "training":
            def _train(cx, cy, cw, ch):
                pyxel.text(cx, cy, "== TRAINING ==", COL_YELLOW)
                for i, (sname, attr) in enumerate(zip(HOME_TRAIN_STATS, HOME_TRAIN_ATTRS)):
                    cur_val = p.perm_stats[attr]
                    cost = (cur_val + 1) * 1000
                    aff = p.gold >= cost
                    cur = ">" if i == self.home_train_idx else " "
                    col = COL_YELLOW if i == self.home_train_idx else COL_WHITE
                    pyxel.text(cx,          cy + 14 + i * 16, f"{cur} {sname} +{cur_val}", col)
                    pyxel.text(cx + cw - 52, cy + 14 + i * 16, f"{cost}G",
                               col if aff else COL_DARK_GRAY)
                pyxel.text(cx, cy + ch - 16, f"Gold: {p.gold}G", COL_YELLOW)
                pyxel.text(cx, cy + ch - 8, "Z:Train  X:Back", COL_DARK_GRAY)
            self.sub_win.draw(_train)

    def _draw_shop(self):
        pyxel.cls(COL_BLACK)

        def _shop_content(cx, cy, cw, ch):
            for i, key in enumerate(SHOP_KEYS):
                item = ITEM_CATALOG[key]
                col = COL_YELLOW if i == self.shop_idx else COL_WHITE
                cursor = ">" if i == self.shop_idx else " "
                affordable = self.player.gold >= item.value
                name_col = col if affordable else COL_DARK_GRAY
                pyxel.text(cx,           cy + i * 14,
                           f"{cursor} {item.name}", name_col)
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
                    pyxel.text(cx,           cy + 16 + i * 14,
                               f"{cursor} {npc.name} [{npc.job.name}]", col)
                    pyxel.text(cx + cw - 40, cy + 16 + i * 14, cost_str,
                               COL_YELLOW if not npc.is_unique else COL_ORANGE)
            pyxel.text(cx, cy + ch - 16,
                       f"Gold: {self.player.gold}G", COL_YELLOW)
            pyxel.text(cx, cy + ch - 8,  "Z:Promote  X:Back", COL_DARK_GRAY)
        self.sub_win.draw(_guild_content)

    def _draw_revive(self):
        pyxel.cls(COL_BLACK)

        def _content(cx, cy, cw, ch):
            pyxel.text(cx, cy, "== TEMPLE of REVIVAL ==", COL_YELLOW)
            fallen = self.party.fallen
            if not fallen:
                pyxel.text(cx, cy + 20, "Everyone is healthy.", COL_GREEN)
                pyxel.text(cx, cy + ch - 8, "Z:Back", COL_DARK_GRAY)
                return
            for i, m in enumerate(fallen):
                cost = m.level * 100
                cursor = ">" if i == self.revive_idx else " "
                affordable = self.player.gold >= cost
                col = COL_WHITE if affordable else COL_DARK_GRAY
                pyxel.text(cx, cy + 20 + i * 14, f"{cursor} {m.name}", col)
                pyxel.text(cx + cw - 40, cy + 20 + i * 14, f"{cost}G",
                           COL_YELLOW if affordable else COL_DARK_GRAY)
            pyxel.text(cx, cy + ch - 16, f"Gold: {self.player.gold}G",
                       COL_YELLOW)
            pyxel.text(cx, cy + ch - 8, "Z:Revive  X:Back", COL_DARK_GRAY)

        self.sub_win.draw(_content)

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

    def draw_npcs(self):
        for npc in self.npcs:
            npc.draw(self.px, self.py, self.dir, is_wall)

    def draw_minimap(self):
        if _dungeon_map is None:
            return
        m = _dungeon_map
        # 1px per tile, placed at bottom-right of dungeon view
        ox = SCREEN_W - m.width - 2   # 234 for width=20
        oy = VIEW_H - m.height - 2  # 154 for height=20
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
                elif tile == TILE_GRAVE:
                    col = COL_PINK
                elif tile == TILE_FOUNTAIN:
                    col = COL_BLUE
                elif tile == TILE_MERCHANT:
                    col = COL_GREEN
                elif tile == TILE_LOCKED_DOOR:
                    col = COL_INDIGO
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
        pyxel.text(SCREEN_W - 4 - len(gold_str) * 4,
                   STATUS_Y + 4, gold_str, COL_YELLOW)
        status_info = f"EXP:{p.exp}/{p.exp_to_next}"
        if p.bonus_points > 0:
            status_info += f"  BP:{p.bonus_points}"
        pyxel.text(4, STATUS_Y + 16, status_info, COL_YELLOW)
        pyxel.text(4, STATUS_Y + 28,
                   f"({self.px},{self.py}) {DIR_NAMES[self.dir]}",
                   COL_LIGHT_GRAY)
        floor_str = f"B{self.dungeon_floor}F"
        pyxel.text(SCREEN_W - 4 - len(floor_str) * 4,
                   STATUS_Y + 28, floor_str, COL_YELLOW)
        pyxel.text(4, STATUS_Y + 40,
                   "Arrow:Move  T:Town  I:Item  S:Skill  Q:Quit", COL_DARK_GRAY)


if __name__ == "__main__":
    App()
