import pyxel
import random
from pathlib import Path
from constants import (
    SCREEN_W, SCREEN_H, FPS, TITLE,
    COL_BLACK, COL_NAVY, COL_DARK_PURPLE, COL_DARK_GREEN, COL_BROWN,
    COL_DARK_GRAY, COL_LIGHT_GRAY, COL_WHITE, COL_RED, COL_ORANGE,
    COL_YELLOW, COL_GREEN, COL_BLUE, COL_INDIGO, COL_PINK, COL_PEACH,
    VIEW_H, STATUS_Y, MAX_DEPTH, MAX_FLOOR,
    FRAMES, WALL_COLS, DUNGEON_MAP, DIR_VECTORS, DIR_NAMES,
    STATE_TOWN, STATE_TOWN_SUB, STATE_DUNGEON,
    STATE_BATTLE_CMD, STATE_BATTLE_MSG, STATE_BATTLE_END,
    STATE_INVENTORY, STATE_INV_ACTION, STATE_SHOP,
    STATE_BATTLE_NPC_CMD, STATE_GUILD, STATE_STAT_ALLOC,
    STATE_BATTLE_TARGET_PART, STATE_BATTLE_TARGET, STATE_REVIVE, STATE_INV_GIVE_NPC,
    STATE_HOME, STATE_ENDING, STATE_DUNGEON_SKILL, STATE_DUNGEON_SHOP,
    STATE_TITLE, STATE_JOB_SELECT, STATE_BATTLE_SKILL, STATE_LOG_VIEW,
    STATE_INV_TARGET_SELECT,
    TILE_FLOOR, TILE_WALL, TILE_STAIRS, TILE_CHEST,
    TILE_TRAP_SPIKE, TILE_TRAP_POISON, TILE_GRAVE, TILE_LOCKED_DOOR,
    TILE_FOUNTAIN, TILE_MERCHANT,
    SAVE_FILE, INV_MAX, SHOP_KEYS, MERCHANT_KEYS, SHOP_COMMANDS,
    SHOP_STOCK_SIZE, SHOP_RESTOCK_STEPS, SHOP_RARE_SLOT_RATE,
    PROMOTION_COST, DROP_RATE, ENCOUNTER_RATE, FLEE_RATE, COMMANDS,
    TOWN_MENU, STAT_ALLOC_NAMES, STAT_ALLOC_ATTRS,
    HOME_MENU, HOME_TRAIN_STATS, HOME_TRAIN_ATTRS,
    HOME_RENOVATE_COSTS, HOME_RENOVATE_SLOTS,
    _BGM_ZONES,
)
from data import (Status, ENEMY_CATALOG, ITEM_CATALOG, JOBS,
                  WeaponItem, ArmorItem, ConsumableItem, AccessoryItem,
                  make_enchanted_weapon, EnchantedWeapon,
                  make_enchanted_armor, EnchantedArmor,
                  NPCMember, Party, ATTR_AFFINITY,
                  Skill, MAX_SKILLS, GrimoireItem, Grave, JOB_SKILLS)
from logic.map_generator import Map
from systems.persistence import save_game, load_game, deserialize_item
from ui.renderer_3d import draw_3d_view as _draw_3d_view
from window import Window
from npc import NPC

# Tier-based drop pools keyed by floor range (1-indexed upper bound inclusive)
_DROP_TIERS = [
    (3,  ["old_dagger", "short_sword", "staff"],          ["leather_armor", "herb", "potion"]),
    (6,  ["long_sword", "chain_mail"],                    ["potion", "ether", "grimoire_ice"]),
    (10, ["steel_sword", "mithril_sword", "steel_plate"], ["ether", "grimoire_poison"]),
]

_SHOP_TIERS = [
    ["short_sword", "staff", "leather_armor", "herb", "potion",
     "antidote", "scroll_mapping", "grimoire_fire", "grimoire_heal",
     "lucky_ring", "emergency_kit"],
    ["long_sword", "chain_mail", "potion", "ether", "antidote",
     "scroll_mapping", "grimoire_heal", "grimoire_ice", "mana_charm",
     "emergency_kit"],
    ["steel_sword", "mithril_sword", "steel_plate", "potion", "ether",
     "antidote", "grimoire_ice", "grimoire_poison", "grimoire_return",
     "rabbits_foot", "emergency_kit"],
]


def _drop_pools(floor):
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


# Global dungeon map (set by _enter_dungeon_fresh / _next_floor)
_dungeon_map = None
LOG_HISTORY_MAX = 100
LOG_VIEW_LINES = 12
LOG_VIEW_STATES = (
    STATE_BATTLE_CMD,
    STATE_BATTLE_NPC_CMD,
    STATE_BATTLE_TARGET,
    STATE_BATTLE_TARGET_PART,
    STATE_BATTLE_SKILL,
    STATE_BATTLE_MSG,
    STATE_BATTLE_END,
)


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
        self.sprite_u = edef.sprite_u
        self.sprite_v = edef.sprite_v
        self.flip_x = random.random() < 0.5


class Effect:
    SPARK_OFFSETS = [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, -4), (0, 4)]

    def __init__(self, x, y, effect_type="spark"):
        self.x = x
        self.y = y
        self.timer = 20
        self.type = effect_type


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title=TITLE, fps=FPS)
        self.sprite_debug_logged = set()
        asset_path = Path(__file__).with_name("assets.pyxres")
        try:
            pyxel.load(str(asset_path))
            self.assets_loaded = True
        except Exception as e:
            self.assets_loaded = False
            print(f"[WARN] assets.pyxres load failed: {e}")
        self.px = 1
        self.py = 1
        self.dir = 1

        self.player = Player()

        # Party (player + up to 3 NPC members)
        self.party = Party(self.player)
        demo_npc = NPCMember("warrior", "Gard", "reckless")
        self.party.add(demo_npc)

        # NPC list (replaced each dungeon entry)
        self.npcs = []

        # Battle state
        self.enemies = []
        self.target_idx = 0
        self._attack_target = None
        self.cmd_idx = 0
        self.messages = []
        self.message_history = []
        self.msg_idx = 0
        self.next_state = None
        self.log_return_state = STATE_BATTLE_CMD
        self.log_scroll = 0
        self.battle_won = False
        self.level_up_gains = []
        self._current_enemy_key = None
        self.telegraphing = {}

        # Damage / heal popups  {"text", "x", "y", "color", "timer"}
        self.popups = []

        # Battle effects (spark, etc.)
        self.effects = []

        # Town state
        self.town_cmd_idx = 0
        self.town_sub_lines = []
        self._dialog_return_state = STATE_TOWN

        # Inventory state
        self.inv_idx = 0
        self.inv_action_idx = 0
        self.inv_actions = []
        self.pre_inv_state = STATE_TOWN
        self.inv_target_idx = 0
        self.pending_use_item = None

        # Shop state
        self.shop_idx  = 0
        self.shop_mode = "buy"
        self.shop_stock = []
        self.steps_to_restock = SHOP_RESTOCK_STEPS

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
        self.bestiary: dict[str, int] = {}
        self.bestiary_idx = 0

        # Battle skill selection
        self.skill_idx = 0
        self._pending_skill = None
        self.steps_since_encounter = 0

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
        self.unlocked_jobs = ["porter"]

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
        self.town_win = Window(8,  10, 240, 125, title="- DELVOKER -")
        self.status_win = Window(8, 143, 240,  86)
        self.sub_win = Window(10, 62, 236, 120)
        self.battle_win = Window(2, 150, SCREEN_W - 4, 88)
        self.inv_win = Window(8,  10, 240, 230, title="- INVENTORY -")
        self.inv_action_win = Window(78, 96, 120,  72, title="Action")
        self.shop_win = Window(8,  10, 240, 230, title="- SHOP -")

        self.state = None
        self._restock_shop(force=True)
        self._init_audio()
        self._set_state(STATE_TITLE)

        pyxel.run(self.update, self.draw)

    # ---- helpers ----

    def add_popup(self, text, x, y, color):
        self.popups.append({"text": text, "x": x, "y": y,
                           "color": color, "timer": 20})

    def _item_label(self, item):
        return item.label() if hasattr(item, "label") else item.name

    def _item_color(self, item, selected=False, enabled=True):
        if not enabled:
            return COL_DARK_GRAY
        rarity = getattr(item, "rarity", "normal")
        if rarity == "genesis":
            return COL_WHITE if (pyxel.frame_count // 10) % 2 == 0 else COL_BLUE
        if rarity == "legend":
            return COL_ORANGE
        if rarity == "epic":
            return COL_PEACH
        if rarity == "rare":
            return COL_YELLOW
        if getattr(item, "is_cursed", False):
            return COL_DARK_PURPLE
        return COL_YELLOW if selected else COL_WHITE

    def _shop_tier_index(self, floor=None):
        floor = self.dungeon_floor if floor is None else floor
        if floor <= 3:
            return 0
        if floor <= 6:
            return 1
        return 2

    def _shop_tier_keys(self, tier_idx=None):
        tier_idx = self._shop_tier_index() if tier_idx is None else tier_idx
        keys = []
        for idx in range(0, min(tier_idx, len(_SHOP_TIERS) - 1) + 1):
            keys.extend(_SHOP_TIERS[idx])
        valid = [k for k in keys if k in SHOP_KEYS and k in ITEM_CATALOG]
        return list(dict.fromkeys(valid))

    def _make_shop_item(self, key, enchanted=False):
        item = ITEM_CATALOG[key]
        if enchanted and item.kind == "weapon":
            return make_enchanted_weapon(key)
        if enchanted and item.kind == "armor":
            return make_enchanted_armor(key)
        return item.clone()

    def _make_rare_shop_item(self):
        tier = self._shop_tier_index()
        upper_keys = self._shop_tier_keys(min(tier + 1, len(_SHOP_TIERS) - 1))
        upper_keys = [k for k in upper_keys if k not in self._shop_tier_keys(tier)]
        gear_keys = [k for k in self._shop_tier_keys(min(tier + 1, len(_SHOP_TIERS) - 1))
                     if ITEM_CATALOG[k].kind in ("weapon", "armor")]
        if upper_keys and random.random() < 0.5:
            return self._make_shop_item(random.choice(upper_keys))
        for _ in range(8):
            key = random.choice(gear_keys or self._shop_tier_keys())
            item = self._make_shop_item(key, enchanted=True)
            if getattr(item, "rarity", "normal") != "normal":
                return item
        return self._make_shop_item(random.choice(gear_keys or self._shop_tier_keys()), enchanted=True)

    def _restock_shop(self, force=False):
        keys = self._shop_tier_keys()
        if not keys:
            self.shop_stock = []
            self.steps_to_restock = SHOP_RESTOCK_STEPS
            return
        if len(keys) >= SHOP_STOCK_SIZE:
            chosen = random.sample(keys, SHOP_STOCK_SIZE)
        else:
            chosen = list(keys)
            while len(chosen) < SHOP_STOCK_SIZE:
                chosen.append(random.choice(keys))
        self.shop_stock = [self._make_shop_item(k) for k in chosen]
        if self.shop_stock and random.random() < SHOP_RARE_SLOT_RATE:
            self.shop_stock[random.randrange(len(self.shop_stock))] = self._make_rare_shop_item()
        self.shop_idx = min(self.shop_idx, max(0, len(self.shop_stock) - 1))
        self.steps_to_restock = SHOP_RESTOCK_STEPS

    def _tick_shop_restock(self):
        self.steps_to_restock -= 1
        if self.steps_to_restock <= 0:
            self._restock_shop()

    def _init_audio(self):
        # SE 0: attack (noise burst)
        pyxel.sounds[0].set("c3", "n", "7", "f", 5)
        # SE 1: hit impact (low noise thud)
        pyxel.sounds[1].set("c1", "n", "6", "f", 8)
        # SE 2: heal arpeggio (rising triangle)
        pyxel.sounds[2].set("c2e2g2c3", "t", "5555", "nnnn", 8)
        # BGM 3: Town (calm triangle melody)
        pyxel.sounds[3].set("e3g3a3g3e3c3d3e3", "t", "3", "n", 18)
        # BGM 4: Dungeon (ominous triangle drone)
        pyxel.sounds[4].set("c2c2a1a1g1g1a1a1", "t", "2", "n", 22)
        # BGM 5: Battle (triangle upbeat)
        pyxel.sounds[5].set("c3e3g3b3c4b3g3e3", "t", "3", "n", 12)
        # pyxel.musics[0].set([3], [], [], [])  # Issue #03: BGM disabled pending replacement
        # pyxel.musics[1].set([4], [], [], [])
        # pyxel.musics[2].set([5], [], [], [])

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
        elif new_state == STATE_INV_TARGET_SELECT:
            self.inv_action_win.close()
            self.sub_win.title = "Use Item"
            self.sub_win.open()
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
            self.shop_mode = "buy"
            self.shop_idx  = 0
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
        self._restock_shop(force=True)

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
            self._grant_job_skill(job_key)
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
                fallen = False
                for member in self.party.members:
                    if member.hp > 0:
                        member.hp = member.max_hp
                        member.mp = member.max_mp
                    else:
                        fallen = True
                self.sub_win.title = "Inn"
                self.town_sub_lines = ["Welcome! Rest well.",
                                       "The party's HP and MP are fully restored."]
                if fallen:
                    self.town_sub_lines.append("Fallen members need Revive.")
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
        if enemy_key:
            keys = [enemy_key]
        else:
            pool = _encounter_pool(self.dungeon_floor)
            f = self.dungeon_floor
            if f <= 2:
                count = 1
            elif f <= 5:
                count = 2 if random.random() < 0.30 else 1
            else:
                r = random.random()
                count = 3 if r < 0.10 else (2 if r < 0.40 else 1)
            keys = [random.choice(pool) for _ in range(count)]
        self.enemies = []
        for k in keys:
            e = Enemy(ENEMY_CATALOG[k])
            e.enemy_key = k
            self.enemies.append(e)
        self._current_enemy_key = keys[0]
        self.telegraphing = {}
        self.target_idx = 0
        self._attack_target = None
        self.cmd_idx = 0
        self.steps_since_encounter = 0
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
        # Provoke forces all enemies to target the player
        if self.player.status_effects.get("provoke", 0) > 0:
            return self.player
        edef = ENEMY_CATALOG.get(
            self._current_enemy_key) if self._current_enemy_key else None
        ai_type = edef.ai_type if edef else "normal"
        if ai_type == "ranged":
            return max(alive, key=lambda m: m.agi)
        if ai_type == "support":
            return min(alive, key=lambda m: m.hp)
        return random.choice(alive)  # normal: random party member

    def _npc_combat_action(self, npc, msgs, enemy_target=None):
        etgt = enemy_target or (self.enemies[0] if self.enemies else None)
        if etgt is None:
            return
        p = npc.personality

        if p == "reckless":
            attack_skills = [s for s in npc.skills
                             if s.effect_type == "attack" and npc.mp >= s.mp_cost]
            if attack_skills and random.random() < 0.40:
                skill = random.choice(attack_skills)
                npc.mp -= skill.mp_cost
                dmg = max(1, skill.power + npc.mag)
                etgt.hp = max(0, etgt.hp - dmg)
                msgs.append(
                    f"[Skill] {npc.name} uses {skill.name}! {etgt.name}: -{dmg} HP!")
            else:
                dmg = self._calc_dmg(npc.weapon, etgt.def_, etgt)
                etgt.hp = max(0, etgt.hp - dmg)
                msgs.append(
                    f"[Reckless] {npc.name} attacks! {etgt.name}: -{dmg} HP!")

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
                    etgt.hp = max(0, etgt.hp - dmg)
                    msgs.append(
                        f"[Skill] {npc.name} uses {skill.name}! {etgt.name}: -{dmg} HP!")
                else:
                    alive = self.party.alive
                    if alive:
                        target = min(alive, key=lambda m: m.hp)
                        heal = skill.power
                        target.hp = min(target.max_hp, target.hp + heal)
                        msgs.append(
                            f"[Skill] {npc.name} uses {skill.name}! {target.name}: +{heal} HP!")
            else:
                dmg = self._calc_dmg(npc.weapon, etgt.def_, etgt)
                etgt.hp = max(0, etgt.hp - dmg)
                msgs.append(f"{npc.name} attacks! {etgt.name}: -{dmg} HP!")

    def _handle_victory(self, msgs, enemy=None):
        if enemy and enemy in self.enemies:
            self.enemies.remove(enemy)
        ekey = getattr(enemy, "enemy_key", None)
        if ekey:
            self.bestiary[ekey] = self.bestiary.get(ekey, 0) + 1
        exp = enemy.exp_reward if enemy else 0
        gold = enemy.gold_reward if enemy else 0
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
        if enemy and self._current_enemy_key:
            edef = ENEMY_CATALOG.get(self._current_enemy_key)
            if edef:
                for p in edef.parts:
                    if p["name"] in enemy.broken_parts and random.random() < 0.2:
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
        target = self.enemies[0] if self.enemies else None
        for npc in self.party.alive[1:]:
            if getattr(npc, "is_unique", False):
                continue
            if not target or target.hp <= 0:
                break
            self._npc_combat_action(npc, msgs, target)
        if target and target.hp <= 0:
            self._handle_victory(msgs, target)
        elif self.enemies:
            self._enemy_turn(msgs)

    def _player_attack(self, enemy=None, part_name=None):
        if enemy is None:
            enemy = self.enemies[0] if self.enemies else None
        if enemy is None:
            return
        pyxel.play(0, 0)
        dmg = self._calc_dmg(self.player.weapon, enemy.def_, enemy)
        dmg = max(1, dmg + self.player.perm_stats["str"])
        is_crit = random.random() < self.player.total_luk / 100
        if is_crit:
            dmg *= 2
        enemy.hp = max(0, enemy.hp - dmg)
        pyxel.play(1, 1)

        attr = getattr(self.player.weapon, "attribute", None)
        popup_col = COL_PINK if is_crit else (
            COL_YELLOW if (attr and attr in enemy.weaknesses) else COL_WHITE)
        self.add_popup(f"-{dmg}", 116, 68, popup_col)
        self.effects.append(Effect(128, 63, "spark"))

        _aid_verbs = [
            "distracts", "taunts", "harasses", "baits", "lures",
            "throws debris at", "feints against", "bluffs at",
        ]
        _aid_verb = _aid_verbs[pyxel.frame_count % len(_aid_verbs)]
        if is_crit:
            msgs = [f"[CRITICAL!] {self.player.name} {_aid_verb} {enemy.name}! -{dmg} HP!"]
        else:
            msgs = [f"{self.player.name} {_aid_verb} {enemy.name}! -{dmg} HP!"]

        if part_name and part_name in enemy.part_hps and part_name not in enemy.broken_parts:
            enemy.part_hps[part_name] = max(
                0, enemy.part_hps[part_name] - dmg)
            if enemy.part_hps[part_name] <= 0:
                enemy.broken_parts.add(part_name)
                msgs.append(f"[PART BROKEN: {part_name}]")

        if enemy.hp <= 0:
            self._handle_victory(msgs, enemy)
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
        for acting_enemy in list(self.enemies):
            edef = ENEMY_CATALOG.get(
                getattr(acting_enemy, "enemy_key", self._current_enemy_key))

            eid = id(acting_enemy)
            # Boss telegraph: show warning turn before power attack
            if edef and edef.telegraph_message and not self.telegraphing.get(eid) and random.random() < 0.3:
                self.telegraphing[eid] = True
                msgs.append(edef.telegraph_message)
                self._show_msgs(msgs, STATE_BATTLE_CMD)
                return

            power_mult = 2 if self.telegraphing.pop(eid, False) else 1

            pyxel.play(0, 0)
            target = self._get_enemy_target()
            base_dmg = self._calc_dmg(acting_enemy.weapon, target.total_def, target)
            dmg = int(base_dmg * power_mult)
            # Provoke: 25% damage reduction while active
            if target is self.player and self.player.status_effects.get("provoke", 0) > 0:
                dmg = int(dmg * 0.75)
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

        # Provoke: tick down at end of each enemy turn round
        prov = self.player.status_effects.get("provoke", 0)
        if prov > 0:
            self.player.status_effects["provoke"] = prov - 1

        # Poison damage at end of turn (once per round, not per enemy)
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

    def _build_part_targets(self, enemy=None):
        e = enemy or (self.enemies[0] if self.enemies else None)
        targets = ["Body"]
        if e:
            for p in e.parts:
                if p["name"] not in e.broken_parts:
                    targets.append(p["name"])
        return targets

    def _upd_battle_target(self):
        alive = [e for e in self.enemies if e.hp > 0]
        if not alive:
            self.state = STATE_BATTLE_CMD
            return
        if pyxel.btnp(pyxel.KEY_X):
            self._pending_skill = None
            self.state = STATE_BATTLE_CMD
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.target_idx = (self.target_idx - 1) % len(alive)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.target_idx = (self.target_idx + 1) % len(alive)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self._attack_target = alive[self.target_idx]
            if self._pending_skill:
                sk = self._pending_skill
                self._pending_skill = None
                self._execute_active_skill(sk, self._attack_target)
            else:
                parts = self._build_part_targets(self._attack_target)
                if len(parts) > 1:
                    self._part_targets = parts
                    self.part_idx = 0
                    self.state = STATE_BATTLE_TARGET_PART
                else:
                    self.state = STATE_BATTLE_CMD
                    self._player_attack(self._attack_target)

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
            target = self._attack_target or (self.enemies[0] if self.enemies else None)
            self.state = STATE_BATTLE_CMD
            self._player_attack(target, part_name)

    def _grant_job_skill(self, job_key):
        """Grant the job's initial skill to the player if not already learned."""
        skill_proto = JOB_SKILLS.get(job_key)
        if skill_proto is None:
            return
        already = any(s.name == skill_proto.name for s in self.player.skills)
        if not already and len(self.player.skills) < MAX_SKILLS:
            from data import Skill as _Skill
            self.player.skills.append(
                _Skill(skill_proto.name, skill_proto.mp_cost,
                       skill_proto.effect_type, skill_proto.power))

    def _try_flee(self):
        if self._current_enemy_key in ("dungeon_master", "archdemon"):
            self._enemy_turn(["You cannot escape!"])
            return
        flee_rate = min(0.95, FLEE_RATE + self.player.total_luk * 0.01)
        if random.random() < flee_rate:
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

    def _append_message_history(self, messages):
        for msg in messages:
            if msg:
                self.message_history.append(msg)
        if len(self.message_history) > LOG_HISTORY_MAX:
            self.message_history = self.message_history[-LOG_HISTORY_MAX:]

    def _open_log_view(self):
        self.log_return_state = self.state
        max_scroll = max(0, len(self.message_history) - LOG_VIEW_LINES)
        self.log_scroll = max_scroll
        self.state = STATE_LOG_VIEW

    def _show_msgs(self, messages, next_state, colors=None):
        self._append_message_history(messages)
        self.messages = messages
        self.msg_colors = colors or []
        self.msg_idx = 0
        self.next_state = next_state
        self.state = STATE_BATTLE_MSG

    # ---- Update ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if self.state == STATE_LOG_VIEW:
            self._upd_log_view()
            return
        if self.state in LOG_VIEW_STATES and pyxel.btnp(pyxel.KEY_L):
            self._open_log_view()
            return

        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.shake_timer > 0:
            self.shake_timer -= 1

        # Tick popups
        self.popups = [p for p in self.popups if p["timer"] > 0]
        for p in self.popups:
            p["timer"] -= 1

        # Tick effects
        self.effects = [e for e in self.effects if e.timer > 0]
        for e in self.effects:
            e.timer -= 1

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
        elif self.state == STATE_INV_TARGET_SELECT:
            self._upd_inv_target_select()
        elif self.state == STATE_SHOP:
            self._upd_shop()
        elif self.state == STATE_GUILD:
            self._upd_guild()
        elif self.state == STATE_STAT_ALLOC:
            self._upd_stat_alloc()
        elif self.state == STATE_BATTLE_TARGET:
            self._upd_battle_target()
        elif self.state == STATE_BATTLE_SKILL:
            self._upd_battle_skill()
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

    def _upd_log_view(self):
        total = len(self.message_history)
        max_scroll = max(0, total - LOG_VIEW_LINES)
        if pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.KEY_L):
            self.state = self.log_return_state
            return
        if total == 0:
            self.log_scroll = 0
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.log_scroll = max(0, self.log_scroll - 1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.log_scroll = min(max_scroll, self.log_scroll + 1)
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.log_scroll = max(0, self.log_scroll - LOG_VIEW_LINES)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.log_scroll = min(max_scroll, self.log_scroll + LOG_VIEW_LINES)

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
            self.steps_since_encounter += 1
            self._tick_shop_restock()
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
            if self.steps_since_encounter >= 4:
                rate = ENCOUNTER_RATE * min(1.0, (self.steps_since_encounter - 3) / 7.0)
                if random.random() < rate:
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
            etgt = self.enemies[0] if self.enemies else None
            if self.npc_cmd_idx == 0 and etgt:  # Aid
                dmg = self._calc_dmg(npc.weapon, etgt.def_, etgt)
                etgt.hp = max(0, etgt.hp - dmg)
                self._round_msgs.append(
                    f"{npc.name} attacks! {etgt.name}: -{dmg} HP!")
            else:  # Retreat
                self._round_msgs.append(f"{npc.name} holds back.")

            if etgt and etgt.hp <= 0:
                self._handle_victory(self._round_msgs, etgt)
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
            if self.cmd_idx == 0:  # Aid
                if len(self.enemies) > 1:
                    self.target_idx = 0
                    self.state = STATE_BATTLE_TARGET
                else:
                    enemy = self.enemies[0] if self.enemies else None
                    if enemy:
                        self._attack_target = enemy
                        targets = self._build_part_targets(enemy)
                        if len(targets) > 1:
                            self._part_targets = targets
                            self.part_idx = 0
                            self.state = STATE_BATTLE_TARGET_PART
                        else:
                            self._player_attack(enemy)
            elif self.cmd_idx == 1:  # Skill
                if self.player.skills:
                    self.skill_idx = 0
                    self.state = STATE_BATTLE_SKILL
            else:  # Flee
                self._try_flee()

    def _upd_battle_skill(self):
        skills = self.player.skills
        if not skills:
            self.state = STATE_BATTLE_CMD
            return
        if pyxel.btnp(pyxel.KEY_X):
            self.state = STATE_BATTLE_CMD
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.skill_idx = (self.skill_idx - 1) % len(skills)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.skill_idx = (self.skill_idx + 1) % len(skills)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            sk = skills[self.skill_idx]
            if self.player.mp < sk.mp_cost:
                return  # not enough MP; stay on skill screen
            if sk.effect_type in ("provoke", "encourage"):
                self._execute_active_skill(sk)
            else:
                if len(self.enemies) > 1:
                    self._pending_skill = sk
                    self.target_idx = 0
                    self.state = STATE_BATTLE_TARGET
                else:
                    enemy = self.enemies[0] if self.enemies else None
                    if enemy:
                        self._execute_active_skill(sk, enemy)

    def _execute_active_skill(self, skill, target=None):
        p = self.player
        p.mp -= skill.mp_cost
        msgs = []
        if skill.effect_type == "encourage":
            heal = skill.power + p.total_luk // 2
            names = []
            for m in self.party.alive:
                m.hp = min(m.max_hp, m.hp + heal)
                names.append(m.name)
            msgs = [f"[Encourage] {p.name} cheers the party! +{heal} HP!",
                    f"Restored: {', '.join(names)}"]
            self._run_auto_and_enemy(msgs)
        elif skill.effect_type == "provoke":
            p.status_effects["provoke"] = skill.power
            msgs = [f"{p.name} uses Provoke! Enemies focus on {p.name}! (-25% dmg)"]
            self._run_auto_and_enemy(msgs)
        elif skill.effect_type == "quick_strike":
            dmg = max(1, p.weapon.roll_damage() + p.agi // 2)
            target.hp = max(0, target.hp - dmg)
            msgs = [f"[Quick Strike] {target.name}: -{dmg} HP!"]
            if target.hp <= 0:
                self._handle_victory(msgs, target)
            else:
                self._run_auto_and_enemy(msgs)
        elif skill.effect_type == "mana_bolt":
            dmg = max(1, p.mag * skill.power)
            target.hp = max(0, target.hp - dmg)
            msgs = [f"[Mana Bolt] {target.name}: -{dmg} HP!"]
            if target.hp <= 0:
                self._handle_victory(msgs, target)
            else:
                self._run_auto_and_enemy(msgs)
        else:  # generic grimoire attack
            dmg = max(1, skill.power + p.mag)
            target.hp = max(0, target.hp - dmg)
            msgs = [f"[{skill.name}] {target.name}: -{dmg} HP!"]
            if target.hp <= 0:
                self._handle_victory(msgs, target)
            else:
                self._run_auto_and_enemy(msgs)

    def _upd_battle_msg(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self.msg_idx += 1
            if self.msg_idx >= len(self.messages):
                ns = self.next_state
                if ns in (STATE_DUNGEON, STATE_TOWN, STATE_ENDING):
                    self.enemies = []
                    self._set_state(ns)
                else:
                    self.state = ns

    def _upd_battle_end(self):
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self.enemies = []
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
            elif item.kind in ("weapon", "armor", "accessory") and npc_members:
                self.inv_actions = ["Equip", "Manage NPC Gear", "Drop", "Cancel"]
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
                if self._use_needs_target(item):
                    self.pending_use_item = item
                    self.inv_target_idx = 0
                    self._set_state(STATE_INV_TARGET_SELECT)
                    return
                if self._do_use(item, self.player):
                    return
            elif sel == "Drop":
                self.player.inventory.remove(item)
                self.inv_idx = min(self.inv_idx, max(
                    0, len(self.player.inventory) - 1))
            elif sel == "Manage NPC Gear":
                self.give_npc_item = item
                self.give_npc_idx = 0
                self._set_state(STATE_INV_GIVE_NPC)
                return
            self._set_state(STATE_INVENTORY)

    def _use_needs_target(self, item):
        return (item.kind == "consumable"
                and not isinstance(item, GrimoireItem)
                and item.name != "Scroll: Mapping")

    def _item_targets(self, item):
        return list(self.party.members)

    def _can_use_item_on(self, item, target):
        if not target or target.hp <= 0:
            return False
        hp_ok = getattr(item, "hp_restore", 0) > 0 and target.hp < target.max_hp
        max_mp = getattr(target, "max_mp", 0)
        mp_ok = getattr(item, "mp_restore", 0) > 0 and target.mp < max_mp
        cure = getattr(item, "cure_status", "")
        cure_ok = bool(cure and target.status_effects.get(cure, 0) > 0)
        return hp_ok or mp_ok or cure_ok

    def _party_card_popup_pos(self, target):
        try:
            idx = self.party.members.index(target)
        except ValueError:
            idx = 0
        card_w = SCREEN_W // Party.MAX_SIZE
        x = idx * card_w + card_w // 2 - 8
        return x, STATUS_Y + 12

    def _upd_inv_target_select(self):
        item = self.pending_use_item
        targets = self._item_targets(item) if item else []
        if pyxel.btnp(pyxel.KEY_X):
            self.pending_use_item = None
            self._set_state(STATE_INV_ACTION)
            return
        if not item or not targets:
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                self.pending_use_item = None
                self._set_state(STATE_INVENTORY)
            return
        self.inv_target_idx = min(self.inv_target_idx, len(targets) - 1)
        if pyxel.btnp(pyxel.KEY_UP):
            self.inv_target_idx = (self.inv_target_idx - 1) % len(targets)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.inv_target_idx = (self.inv_target_idx + 1) % len(targets)
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            target = targets[self.inv_target_idx]
            if not self._can_use_item_on(item, target):
                self.sub_win.title = "Use Item"
                return
            self._do_use(item, target)
            self.pending_use_item = None
            self._set_state(STATE_INVENTORY)

    def _do_equip(self, item):
        p = self.player
        wc = getattr(item, "weight_class", "light")
        if wc == "heavy":
            self.town_sub_lines = ["Too heavy for a Porter!", "Cannot equip heavy gear."]
            self.sub_win.title = "EQUIP"
            self._dialog_return_state = STATE_INV_ACTION
            self._set_state(STATE_TOWN_SUB)
            return
        if item.kind == "weapon":
            if p.weapon:
                p.inventory.append(p.weapon)
            p.weapon = item
        elif item.kind == "armor":
            if p.armor:
                p.inventory.append(p.armor)
            p.armor = item
        elif item.kind == "accessory":
            if p.accessory:
                p.inventory.append(p.accessory)
            p.accessory = item
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
            elif item.kind == "accessory":
                old_item = getattr(npc, "accessory", None)
                p.inventory.remove(item)
                npc.accessory = item
                if old_item:
                    p.inventory.append(old_item)
            self.inv_idx = min(self.inv_idx, max(0, len(p.inventory) - 1))
            self.give_npc_item = None
            self._set_state(STATE_INVENTORY)

    def _do_use(self, item, target=None):
        p = self.player
        target = target or p
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
            if not self._can_use_item_on(item, target):
                return False
            heal_hp = min(target.max_hp - target.hp, item.hp_restore)
            heal_mp = min(target.max_mp - target.mp, item.mp_restore)
            target.hp = min(target.max_hp, target.hp + item.hp_restore)
            target.mp = min(target.max_mp, target.mp + item.mp_restore)
            played_se = False
            if heal_hp > 0:
                px, py = self._party_card_popup_pos(target)
                self.add_popup(f"+{heal_hp}", px, py, COL_GREEN)
                pyxel.play(2, 2)
                played_se = True
            if heal_mp > 0 and not played_se:
                pyxel.play(2, 2)
                played_se = True
            cure = getattr(item, "cure_status", "")
            if cure and target.status_effects.get(cure, 0) > 0:
                target.status_effects[cure] = 0
                if not played_se:
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
                elif sel == "Bestiary":
                    self.home_sub = "bestiary"
                    self.bestiary_idx = 0
                    self.sub_win.close()
                    self.inv_win.title = "== BESTIARY =="
                    self.inv_win.open()
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

        elif sub == "bestiary":
            if pyxel.btnp(pyxel.KEY_X):
                self.home_sub = "menu"
                self.inv_win.title = "- INVENTORY -"
                self.inv_win.close()
                self.sub_win.open()
                return
            discovered = [k for k in ENEMY_CATALOG if self.bestiary.get(k, 0) > 0]
            if discovered:
                if pyxel.btnp(pyxel.KEY_UP):
                    self.bestiary_idx = (self.bestiary_idx - 1) % len(discovered)
                if pyxel.btnp(pyxel.KEY_DOWN):
                    self.bestiary_idx = (self.bestiary_idx + 1) % len(discovered)
                self.bestiary_idx = min(self.bestiary_idx, len(discovered) - 1)

    # ---- Persistence ----

    def save_data(self):
        save_game(self.player, self.unlocked_jobs, self.game_cleared, bestiary=self.bestiary)

    def load_data(self):
        data = load_game()
        if not data:
            return
        self.player.gold = data.get("gold", 0)
        self.player.warehouse = [deserialize_item(d)
                                 for d in data.get("warehouse", [])]
        self.player.warehouse_max = data.get("warehouse_max", 10)
        self.player.perm_stats = data.get("perm_stats", {"str": 0, "def": 0, "mag": 0})
        self.unlocked_jobs = data.get("unlocked_jobs", ["porter"])
        self.game_cleared = data.get("game_cleared", False)
        self.bestiary = data.get("bestiary", {})

    # ---- Shop logic ----

    def _upd_shop(self):
        if pyxel.btnp(pyxel.KEY_X):
            self._set_state(STATE_TOWN)
            return
        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT):
            self.shop_mode = "sell" if self.shop_mode == "buy" else "buy"
            self.shop_idx = 0
            return
        if self.shop_mode == "buy":
            if not self.shop_stock:
                self._restock_shop(force=True)
            if not self.shop_stock:
                return
            if pyxel.btnp(pyxel.KEY_UP):
                self.shop_idx = (self.shop_idx - 1) % len(self.shop_stock)
            if pyxel.btnp(pyxel.KEY_DOWN):
                self.shop_idx = (self.shop_idx + 1) % len(self.shop_stock)
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                if len(self.player.inventory) >= INV_MAX:
                    return
                item = self.shop_stock[self.shop_idx]
                if self.player.gold >= item.value:
                    self.player.gold -= item.value
                    self.player.inventory.append(item.clone())
        else:
            inv = self.player.inventory
            if not inv:
                return
            self.shop_idx = min(self.shop_idx, len(inv) - 1)
            if pyxel.btnp(pyxel.KEY_UP):
                self.shop_idx = (self.shop_idx - 1) % len(inv)
            if pyxel.btnp(pyxel.KEY_DOWN):
                self.shop_idx = (self.shop_idx + 1) % len(inv)
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
                item = inv[self.shop_idx]
                if item is self.player.weapon or item is self.player.armor or item is self.player.accessory:
                    return
                sell_price = int(item.value * 0.3)
                self.player.gold += sell_price
                inv.pop(self.shop_idx)
                self.shop_idx = min(self.shop_idx, max(0, len(inv) - 1))

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
        elif self.state in (STATE_INVENTORY, STATE_INV_ACTION, STATE_INV_GIVE_NPC,
                            STATE_INV_TARGET_SELECT):
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
        elif self.state == STATE_LOG_VIEW:
            self._draw_battle()
            self._draw_log_view()
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
                cx, cy,     f"{p.name}  Lv{p.level} {p.job.name}  LUK:{p.total_luk}", COL_WHITE)
            pyxel.text(
                cx, cy+12,  f"HP: {p.hp}/{p.max_hp}   MP: {p.mp}/{p.total_max_mp}", COL_GREEN)
            pyxel.text(
                cx, cy+24,  f"EXP: {p.exp}/{p.exp_to_next}   Gold: {p.gold}", COL_YELLOW)
            pyxel.text(cx, cy+36, f"W: {p.weapon.label()}", COL_PEACH)
            armor_name = p.armor.label() if p.armor else "None"
            pyxel.text(cx, cy+46, f"A: {armor_name}", COL_PEACH)
            acc_name = p.accessory.label() if p.accessory else "None"
            pyxel.text(cx, cy+56, f"Acc: {acc_name}", COL_PEACH)
            if p.bonus_points > 0:
                pyxel.text(
                    cx, cy+66, f"Bonus Points: {p.bonus_points}  (Stats menu)", COL_ORANGE)

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

    def _enemy_palette_swaps(self, enemy):
        key = getattr(enemy, "enemy_key", "")
        if key in ("dungeon_master", "archdemon", "orc_chief"):
            return [(COL_GREEN, COL_PINK), (COL_DARK_GREEN, COL_DARK_PURPLE),
                    (COL_RED, COL_ORANGE)]
        if self.dungeon_floor <= 3:
            return []
        if self.dungeon_floor <= 6:
            return [(COL_GREEN, COL_BLUE), (COL_DARK_GREEN, COL_NAVY),
                    (COL_RED, COL_INDIGO)]
        return [(COL_GREEN, COL_RED), (COL_DARK_GREEN, COL_DARK_PURPLE),
                (COL_BLUE, COL_ORANGE)]

    def _sprite_warn_once(self, key, message):
        if key in self.sprite_debug_logged:
            return
        self.sprite_debug_logged.add(key)
        print(f"[WARN] {message}")

    def _draw_enemy_fallback(self, enemy, x, y, reason="fallback"):
        key = getattr(enemy, "enemy_key", getattr(enemy, "name", "enemy"))
        log_key = (key, reason)
        if reason:
            self._sprite_warn_once(
                log_key,
                f"enemy sprite {reason}: key={key} "
                f"u={getattr(enemy, 'sprite_u', None)} "
                f"v={getattr(enemy, 'sprite_v', None)} x={x} y={y} "
                f"assets_loaded={self.assets_loaded}"
            )
        rect_col = COL_DARK_GRAY if enemy.hp <= 0 else COL_RED
        pyxel.rect(x, y, 32, 32, rect_col)
        pyxel.rectb(x, y, 32, 32, COL_WHITE)
        label = getattr(enemy, "name", "?")[:1].upper()
        pyxel.text(x + 14, y + 13, label, COL_WHITE)

    def _draw_enemy_sprite(self, enemy, x, y):
        if not self.assets_loaded:
            self._draw_enemy_fallback(enemy, x, y, "assets_not_loaded")
            return False
        sprite_u = getattr(enemy, "sprite_u", None)
        sprite_v = getattr(enemy, "sprite_v", None)
        if sprite_u is None or sprite_v is None or sprite_u < 0 or sprite_v < 0:
            self._draw_enemy_fallback(enemy, x, y, "invalid_coords")
            return False
        try:
            for orig, new in self._enemy_palette_swaps(enemy):
                if 0 <= orig <= 15 and 0 <= new <= 15 and new != COL_BLACK:
                    pyxel.pal(orig, new)
            if enemy.flip_x:
                pyxel.blt(x + 32, y, 0, sprite_u, sprite_v, -32, 32, 0)
            else:
                pyxel.blt(x, y, 0, sprite_u, sprite_v, 32, 32, 0)
            return True
        except Exception as e:
            pyxel.pal()
            self._draw_enemy_fallback(enemy, x, y, f"blt_failed:{e}")
            return False
        finally:
            pyxel.pal()

    def _draw_battle(self):
        pyxel.cls(COL_BLACK)

        # Enemy area — distribute enemies horizontally
        n = max(len(self.enemies), 1)
        slot_w = SCREEN_W // n
        ey, eh = 28, 64
        alive_for_target = [e for e in self.enemies if e.hp > 0]

        for i, enemy in enumerate(self.enemies):
            cx = slot_w // 2 + i * slot_w  # horizontal center of this slot

            # Name
            name_x = max(0, cx - len(enemy.name) * 2)
            col_name = COL_LIGHT_GRAY if enemy.hp <= 0 else COL_WHITE
            pyxel.text(name_x, ey - 10, enemy.name, col_name)

            # Sprite / fallback rect
            sprite_x = cx - 16
            sprite_y = ey + (eh - 32) // 2
            self._draw_enemy_sprite(enemy, sprite_x, sprite_y)

            # HP bar
            bar_w = min(80, slot_w - 4)
            bx = cx - bar_w // 2
            by = ey + eh + 2
            e_hp_f = enemy.hp / enemy.max_hp if enemy.max_hp > 0 else 0
            pyxel.rect(bx, by, bar_w, 3, COL_DARK_GRAY)
            pyxel.rect(bx, by, int(bar_w * e_hp_f), 3, COL_GREEN)
            pyxel.text(bx, by + 5, f"HP {enemy.hp}/{enemy.max_hp}", COL_LIGHT_GRAY)

            # Target cursor (STATE_BATTLE_TARGET)
            if (self.state == STATE_BATTLE_TARGET and
                    enemy in alive_for_target and
                    alive_for_target.index(enemy) == self.target_idx):
                pyxel.text(cx - 4, by + 14, "^", COL_YELLOW)

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
        npc_slot_w = 84
        for i, npc in enumerate(self.party.members[1:]):
            npc_col = COL_GREEN if npc.hp > npc.max_hp * \
                0.4 else (COL_ORANGE if npc.hp > 0 else COL_RED)
            npc_x = 4 + i * npc_slot_w
            pyxel.text(npc_x, 142,
                       f"{npc.name[:5]} HP:{npc.hp}/{npc.max_hp}", npc_col)
            npc_icon_x = npc_x + 58
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
                    for si, sk in enumerate(p.skills):
                        gx = cx + (si % 2) * 60
                        gy = cy + 52 + (si // 2) * 8
                        pyxel.text(gx, gy, sk.name[:9], COL_INDIGO)
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
            elif self.state == STATE_BATTLE_SKILL:
                p_skills = p.skills
                pyxel.text(cx, cy, "Choose skill:", COL_YELLOW)
                for i, sk in enumerate(p_skills):
                    can_use = p.mp >= sk.mp_cost
                    col = COL_YELLOW if i == self.skill_idx else (COL_WHITE if can_use else COL_DARK_GRAY)
                    cur = ">" if i == self.skill_idx else " "
                    pyxel.text(cx, cy + 12 + i * 14,
                               f"{cur} {sk.name[:10]}  MP:{sk.mp_cost}", col)
                pyxel.text(cx, cy + ch - 20, f"MP: {p.mp}/{p.max_mp}", COL_BLUE)
                pyxel.text(6, cy + ch - 8,
                           "Z:OK  X:Cancel  Up/Down:Select", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_TARGET:
                pyxel.text(cx, cy, "Choose target:", COL_YELLOW)
                for i, e in enumerate(alive_for_target):
                    col = COL_YELLOW if i == self.target_idx else COL_WHITE
                    cur = ">" if i == self.target_idx else " "
                    pyxel.text(cx, cy + 12 + i * 14, f"{cur} {e.name}", col)
                pyxel.text(6, cy + ch - 8,
                           "Z:OK  X:Cancel  Up/Down:Select", COL_DARK_GRAY)
            elif self.state == STATE_BATTLE_TARGET_PART:
                tgt_enemy = self._attack_target or (self.enemies[0] if self.enemies else None)
                pyxel.text(cx, cy, "Target:", COL_YELLOW)
                for i, t in enumerate(self._part_targets):
                    col = COL_YELLOW if i == self.part_idx else COL_WHITE
                    cur = ">" if i == self.part_idx else " "
                    hp_info = ""
                    if t != "Body" and tgt_enemy and t in tgt_enemy.part_hps:
                        hp_info = f" HP:{tgt_enemy.part_hps[t]}"
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
                        if lu.get("luk", 0) > 0:
                            parts.append("LUK+1")
                        pyxel.text(cx, cy + 34, "  ".join(parts), COL_PEACH)
                else:
                    pyxel.text(cx + (cw - 44) // 2, cy +
                               14, "DEFEATED...", COL_RED)
                    pyxel.text(cx + (cw - 80) // 2, cy + 28,
                               "Returning to town...", COL_DARK_GRAY)
                pyxel.text(SCREEN_W - 82, cy + ch - 8,
                           "Z:Continue", COL_DARK_GRAY)

        self.battle_win.draw(_panel_content)

        # Hit effects (spark)
        for eff in self.effects:
            fade = eff.timer > 10
            col = COL_YELLOW if fade else COL_ORANGE
            for dx, dy in Effect.SPARK_OFFSETS:
                pyxel.pset(eff.x + dx, eff.y + dy, col)

        # Damage / heal popups (float upward)
        for pop in self.popups:
            float_y = pop["y"] - (20 - pop["timer"])
            pyxel.text(pop["x"], float_y, pop["text"], pop["color"])

    def _draw_log_view(self):
        x, y, w, h = 10, 18, SCREEN_W - 20, 142
        pyxel.rect(x, y, w, h, COL_BLACK)
        pyxel.rectb(x, y, w, h, COL_WHITE)
        pyxel.text(x + 8, y + 6, "BATTLE LOG", COL_YELLOW)
        pyxel.text(x + w - 78, y + 6, "L/X:Close", COL_DARK_GRAY)

        lines = self.message_history
        if not lines:
            pyxel.text(x + 8, y + 24, "No logs.", COL_DARK_GRAY)
        else:
            start = min(self.log_scroll, max(0, len(lines) - LOG_VIEW_LINES))
            visible = lines[start:start + LOG_VIEW_LINES]
            for i, txt in enumerate(visible):
                pyxel.text(x + 8, y + 22 + i * 9, txt[:54], self._msg_color(txt))
            pos = f"{start + 1}-{start + len(visible)}/{len(lines)}"
            pyxel.text(x + w - len(pos) * 4 - 8, y + h - 10, pos, COL_LIGHT_GRAY)
        pyxel.text(x + 8, y + h - 10, "Up/Down:Scroll  Left/Right:Page", COL_DARK_GRAY)

    def _draw_inventory(self):
        pyxel.cls(COL_BLACK)

        def _inv_content(cx, cy, cw, ch):
            inv = self.player.inventory
            if not inv:
                pyxel.text(cx, cy + 40, "-- Empty --", COL_DARK_GRAY)
            else:
                for i, item in enumerate(inv):
                    cursor = ">" if i == self.inv_idx else " "
                    eq = item is self.player.weapon or item is self.player.armor or item is self.player.accessory
                    tag = {"weapon": "W", "armor": "A",
                           "consumable": "C", "accessory": "Acc"}.get(item.kind, "?")
                    name_col = COL_GREEN if eq else self._item_color(item)
                    display = self._item_label(item)
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
                item = self.give_npc_item
                item_label = f"[{item.kind.upper()}] {item.name[:18]}" if item else ""
                pyxel.text(cx, cy, "== Manage NPC Gear ==", COL_YELLOW)
                pyxel.text(cx, cy + 10, item_label, COL_PEACH)
                npc_members = [m for m in self.party.members[1:]
                               if isinstance(m, NPCMember)]
                if not npc_members:
                    pyxel.text(cx, cy + 24, "No NPC in party.", COL_DARK_GRAY)
                else:
                    row_h = 24
                    for i, npc in enumerate(npc_members):
                        cursor = ">" if i == self.give_npc_idx else " "
                        col = COL_YELLOW if i == self.give_npc_idx else COL_WHITE
                        pyxel.text(cx, cy + 24 + i * row_h,
                                   f"{cursor} {npc.name}", col)
                        npc_wp  = npc.weapon.name[:14]    if npc.weapon    else "None"
                        npc_ar  = npc.armor.name[:14]     if npc.armor     else "None"
                        npc_acc = getattr(npc, "accessory", None)
                        npc_acc = npc_acc.name[:12] if npc_acc else "None"
                        pyxel.text(cx + 8, cy + 24 + i * row_h + 8,
                                   f"W:{npc_wp}  A:{npc_ar}", COL_LIGHT_GRAY)
                        pyxel.text(cx + 8, cy + 24 + i * row_h + 16,
                                   f"Acc:{npc_acc}", COL_LIGHT_GRAY)
                pyxel.text(cx, cy + ch - 8, "Z:Equip  X:Cancel", COL_DARK_GRAY)
            self.sub_win.draw(_npc_sel_content)

        if self.state == STATE_INV_TARGET_SELECT:
            def _target_content(cx, cy, _cw, ch):
                item = self.pending_use_item
                item_name = self._item_label(item)[:24] if item else "None"
                pyxel.text(cx, cy, "== Use Item ==", COL_YELLOW)
                pyxel.text(cx, cy + 10, item_name, COL_PEACH)
                targets = self._item_targets(item) if item else []
                if not targets:
                    pyxel.text(cx, cy + 28, "No targets.", COL_DARK_GRAY)
                for i, target in enumerate(targets):
                    cursor = ">" if i == self.inv_target_idx else " "
                    can_use = self._can_use_item_on(item, target)
                    col = COL_YELLOW if i == self.inv_target_idx and can_use else (
                        COL_WHITE if can_use else COL_DARK_GRAY)
                    pyxel.text(cx, cy + 28 + i * 18,
                               f"{cursor} {target.name[:8]}", col)
                    pyxel.text(cx + 72, cy + 28 + i * 18,
                               f"HP:{target.hp}/{target.max_hp}", col)
                    pyxel.text(cx + 136, cy + 28 + i * 18,
                               f"MP:{target.mp}/{target.max_mp}", col)
                    icons = []
                    if target.status_effects.get("poison", 0) > 0:
                        icons.append("P")
                    if target.status_effects.get("stun", 0) > 0:
                        icons.append("S")
                    if icons:
                        pyxel.text(cx + 190, cy + 28 + i * 18,
                                   "[" + "".join(icons) + "]", COL_ORANGE)
                pyxel.text(cx, cy + ch - 8, "Z:Use  X:Cancel", COL_DARK_GRAY)
            self.sub_win.draw(_target_content)

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
            pyxel.text(px + 4,       py + 18 + i * 14, f"{cursor} {item.name[:18]}", name_col)
            pyxel.text(px + pw - 46, py + 18 + i * 14, f"{price}G",
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
                        pyxel.text(cx, cy + 12 + i * 10, f"{cur}{name[:18]}", col)
                    if i < len(storage):
                        cur = ">" if (self.home_wh_side == 1 and i == self.home_wh_idx) else " "
                        col = COL_YELLOW if (self.home_wh_side == 1 and i == self.home_wh_idx) else COL_WHITE
                        name = storage[i].label() if hasattr(storage[i], "label") else storage[i].name
                        pyxel.text(cx + half + 3, cy + 12 + i * 10, f"{cur}{name[:18]}", col)
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

        elif sub == "bestiary":
            def _bst(cx, cy, cw, ch):
                discovered = [k for k in ENEMY_CATALOG if self.bestiary.get(k, 0) > 0]
                total = len(ENEMY_CATALOG)
                pyxel.text(cx, cy, f"Discovered: {len(discovered)}/{total}", COL_LIGHT_GRAY)
                if not discovered:
                    pyxel.text(cx, cy + 16, "No enemies recorded yet.", COL_DARK_GRAY)
                else:
                    max_rows = (ch - 56) // 10
                    scroll = max(0, self.bestiary_idx - max_rows + 1)
                    for row, i in enumerate(range(scroll, min(scroll + max_rows, len(discovered)))):
                        key = discovered[i]
                        edef = ENEMY_CATALOG[key]
                        cur = ">" if i == self.bestiary_idx else " "
                        col = COL_YELLOW if i == self.bestiary_idx else COL_WHITE
                        kills = self.bestiary.get(key, 0)
                        pyxel.text(cx, cy + 12 + row * 10, f"{cur}{edef.name[:16]}", col)
                        pyxel.text(cx + cw - 38, cy + 12 + row * 10, f"x{kills}", col)
                    # Detail panel for selected enemy
                    if self.bestiary_idx < len(discovered):
                        sel_key = discovered[self.bestiary_idx]
                        edef = ENEMY_CATALOG[sel_key]
                        dy = cy + ch - 46
                        pyxel.line(cx, dy - 2, cx + cw - 1, dy - 2, COL_DARK_GRAY)
                        pyxel.text(cx, dy, f"-- {edef.name} --", COL_YELLOW)
                        pyxel.text(cx, dy + 10, f"HP:{edef.hp}  DEF:{edef.def_}", COL_WHITE)
                        weak_str = "/".join(edef.weaknesses) if edef.weaknesses else "none"
                        res_str = "/".join(edef.resistances) if edef.resistances else "none"
                        pyxel.text(cx, dy + 20, f"Weak:{weak_str}", COL_ORANGE)
                        pyxel.text(cx, dy + 30, f"Res:{res_str}", COL_BLUE)
                pyxel.text(cx, cy + ch - 8, "U/D:Scroll  X:Back", COL_DARK_GRAY)
            self.inv_win.draw(_bst)

    def _draw_shop(self):
        pyxel.cls(COL_BLACK)

        def _shop_content(cx, cy, cw, ch):
            # Mode tabs
            for i, cmd in enumerate(SHOP_COMMANDS):
                tab_col = COL_YELLOW if (cmd.lower() == self.shop_mode) else COL_DARK_GRAY
                pyxel.text(cx + i * 40, cy, f"[{cmd}]", tab_col)
            pyxel.text(cx + len(SHOP_COMMANDS) * 40, cy, "<>:Switch", COL_DARK_GRAY)
            row_y = cy + 12

            p = self.player
            if self.shop_mode == "buy":
                if not self.shop_stock:
                    pyxel.text(cx, row_y, "-- No Stock --", COL_DARK_GRAY)
                for i, item in enumerate(self.shop_stock[:SHOP_STOCK_SIZE]):
                    col_i = i % 3
                    row_i = i // 3
                    cell_x = cx + col_i * 76
                    cell_y = row_y + row_i * 24
                    selected = i == self.shop_idx
                    border_col = COL_YELLOW if selected else COL_DARK_GRAY
                    affordable = p.gold >= item.value
                    name_col = self._item_color(item, selected, affordable)
                    pyxel.rectb(cell_x, cell_y, 72, 21, border_col)
                    cursor = ">" if selected else " "
                    pyxel.text(cell_x + 2, cell_y + 3,
                               f"{cursor}{self._item_label(item)[:14]}", name_col)
                    pyxel.text(cell_x + 2, cell_y + 12, f"{item.value}G",
                               COL_YELLOW if affordable else COL_DARK_GRAY)
                if len(p.inventory) >= INV_MAX:
                    pyxel.text(cx + 60, cy + ch - 16, "Bag Full!", COL_RED)
                pyxel.text(cx + 118, cy + ch - 16,
                           f"Restock:{self.steps_to_restock}", COL_LIGHT_GRAY)
                pyxel.text(cx, cy + ch - 8, "Z:Buy  X:Back  <>:Switch", COL_DARK_GRAY)
            else:
                inv = p.inventory
                if not inv:
                    pyxel.text(cx, row_y, "-- Empty --", COL_DARK_GRAY)
                else:
                    for i, item in enumerate(inv):
                        equipped = (item is p.weapon or item is p.armor or item is p.accessory)
                        col = self._item_color(item, i == self.shop_idx, not equipped)
                        cursor = ">" if i == self.shop_idx else " "
                        sell_price = int(item.value * 0.3)
                        tag = "[E]" if equipped else f"{sell_price}G"
                        pyxel.text(cx,           row_y + i * 10,
                                   f"{cursor} {self._item_label(item)[:16]}", col)
                        pyxel.text(cx + cw - 42, row_y + i * 10, tag, col)
                pyxel.text(cx, cy + ch - 8, "Z:Sell  X:Back", COL_DARK_GRAY)

            pyxel.text(cx, cy + ch - 16, f"Gold: {p.gold}G", COL_YELLOW)

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
        _draw_3d_view(self.wall_at)

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

    def _draw_stat_bar(self, x, y, w, value, max_value, col):
        pyxel.rect(x, y, w, 3, COL_DARK_GRAY)
        fill = 0 if max_value <= 0 else int(w * max(0, value) / max_value)
        pyxel.rect(x, y, min(w, fill), 3, col)

    def _short_item_name(self, item, limit):
        if not item:
            return "None"
        return self._item_label(item).replace(" ", "")[:limit]

    def _draw_party_card(self, member, x, y, w, h, role, border_col):
        pyxel.rect(x, y, w, h, COL_BLACK)
        pyxel.rectb(x, y, w, h, border_col)
        if member is None:
            pyxel.text(x + 8, y + 24, "Empty", COL_DARK_GRAY)
            return
        hp_rate = member.hp / member.max_hp if member.max_hp > 0 else 0
        hp_col = COL_GREEN if hp_rate > 0.4 else (COL_ORANGE if hp_rate > 0.2 else COL_RED)
        name_limit = max(4, (w - len(role) * 4 - 10) // 4)
        name = member.name[:name_limit]
        pyxel.text(x + 3, y + 3, name, COL_WHITE)
        pyxel.text(x + w - len(role) * 4 - 3, y + 3, role, border_col)
        pyxel.text(x + 3, y + 13, f"HP {member.hp}/{member.max_hp}", hp_col)
        self._draw_stat_bar(x + 3, y + 22, w - 6, member.hp, member.max_hp, hp_col)
        max_mp = getattr(member, "total_max_mp", member.max_mp)
        pyxel.text(x + 3, y + 27, f"MP {member.mp}/{max_mp}", COL_BLUE)
        self._draw_stat_bar(x + 3, y + 36, w - 6, member.mp, max_mp, COL_BLUE)
        equip_limit = max(3, min(6, (w - 8) // 8))
        wp = self._short_item_name(getattr(member, "weapon", None), equip_limit)
        ar = self._short_item_name(getattr(member, "armor", None), equip_limit)
        pyxel.text(x + 3, y + 41, f"W:{wp}", COL_PEACH)
        pyxel.text(x + 3, y + 50, f"A:{ar}", COL_PEACH)
        icon_x = x + w - 28
        if member.status_effects.get("poison", 0) > 0:
            pyxel.text(icon_x, y + 50, "[P]", COL_GREEN)
            icon_x += 13
        if member.status_effects.get("stun", 0) > 0:
            pyxel.text(icon_x, y + 50, "[S]", COL_YELLOW)

    def draw_status(self):
        pyxel.rect(0, STATUS_Y, SCREEN_W, SCREEN_H - STATUS_Y, COL_BLACK)
        pyxel.line(0, STATUS_Y, SCREEN_W - 1, STATUS_Y, COL_DARK_GRAY)
        card_y = STATUS_Y + 2
        card_h = 60
        card_count = Party.MAX_SIZE
        card_w = SCREEN_W // card_count
        members = self.party.members[:card_count]
        while len(members) < card_count:
            members.append(None)
        for i, member in enumerate(members):
            x = i * card_w
            w = card_w if i < card_count - 1 else SCREEN_W - x
            role = "[REAR]" if i == 0 else "[FRONT]"
            border = COL_PEACH if i == 0 else COL_LIGHT_GRAY
            self._draw_party_card(member, x + 1, card_y, w - 2, card_h, role, border)
        meta = f"B{self.dungeon_floor}F ({self.px},{self.py}) {DIR_NAMES[self.dir]}  Gold:{self.player.gold}G"
        if self.player.bonus_points > 0:
            meta += f" BP:{self.player.bonus_points}"
        pyxel.text(4, STATUS_Y + 64, meta[:62], COL_YELLOW)
        pyxel.text(4, STATUS_Y + 72,
                   "Arrow:Move  T:Town  I:Item  S:Skill  Q:Quit", COL_DARK_GRAY)


if __name__ == "__main__":
    App()
