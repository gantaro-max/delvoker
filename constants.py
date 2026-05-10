# Screen
SCREEN_W = 256
SCREEN_H = 256
FPS      = 30
TITLE    = "Delvoker"

# Colors (Pyxel palette 0-15)
COL_BLACK       = 0
COL_NAVY        = 1
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

# 3D view geometry
VIEW_H    = 176
STATUS_Y  = VIEW_H
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
DIR_NAMES   = ['N', 'E', 'S', 'W']

# Game states
STATE_TOWN               = 0
STATE_TOWN_SUB           = 1
STATE_DUNGEON            = 2
STATE_BATTLE_CMD         = 3
STATE_BATTLE_MSG         = 4
STATE_BATTLE_END         = 5
STATE_INVENTORY          = 6
STATE_INV_ACTION         = 7
STATE_SHOP               = 8
STATE_BATTLE_NPC_CMD     = 9
STATE_GUILD              = 10
STATE_STAT_ALLOC         = 11
STATE_BATTLE_TARGET_PART = 12
STATE_REVIVE             = 13
STATE_BATTLE_TARGET      = 21
STATE_BATTLE_SKILL       = 22
STATE_INV_GIVE_NPC       = 14
STATE_HOME               = 15
STATE_ENDING             = 16
STATE_DUNGEON_SKILL      = 17
STATE_DUNGEON_SHOP       = 18
STATE_TITLE              = 19
STATE_JOB_SELECT         = 20
STATE_LOG_VIEW           = 23

# Tile types
TILE_FLOOR       = 0
TILE_WALL        = 1
TILE_STAIRS      = 2
TILE_CHEST       = 3
TILE_TRAP_SPIKE  = 4
TILE_TRAP_POISON = 5
TILE_GRAVE       = 6
TILE_LOCKED_DOOR = 7
TILE_FOUNTAIN    = 8
TILE_MERCHANT    = 9

# Persistence
SAVE_FILE = "delvoker_save.json"

# Inventory / shop
INV_MAX       = 12
SHOP_KEYS     = [
    "short_sword", "long_sword", "staff", "leather_armor", "chain_mail",
    "steel_sword", "mithril_sword", "steel_plate",
    "herb", "potion", "ether", "antidote", "scroll_mapping",
    "grimoire_fire", "grimoire_heal", "grimoire_ice", "grimoire_poison", "grimoire_return",
    "lucky_ring", "mana_charm", "rabbits_foot", "emergency_kit",
]
MERCHANT_KEYS  = ["elixir", "potion", "ether", "antidote", "holy_scroll", "grimoire_heal"]
SHOP_COMMANDS  = ["Buy", "Sell"]
SHOP_STOCK_SIZE = 15
SHOP_RESTOCK_STEPS = 100
SHOP_RARE_SLOT_RATE = 0.08

# Battle / progression
PROMOTION_COST = 1000
DROP_RATE      = 0.35
ENCOUNTER_RATE = 0.15
FLEE_RATE      = 0.5
COMMANDS       = ["Aid", "Skill", "Flee"]

# Menus
TOWN_MENU           = ["Inn", "Guild", "Shop", "Stats", "Revive", "Home", "Enter Dungeon"]
STAT_ALLOC_NAMES    = ["STR", "DEF", "AGI", "MAG"]
STAT_ALLOC_ATTRS    = ["str_", "def_", "agi", "mag"]
HOME_MENU           = ["Warehouse", "Renovate", "Training", "Bestiary", "Back"]
HOME_TRAIN_STATS    = ["STR", "DEF", "MAG"]
HOME_TRAIN_ATTRS    = ["str", "def", "mag"]
HOME_RENOVATE_COSTS = [500, 1000, 2000, 4000, 8000]
HOME_RENOVATE_SLOTS = 5

# BGM zone mapping: state -> music index (0=town, 1=dungeon, 2=battle, -1=stop)
_BGM_ZONES = {
    STATE_TITLE: 0,        STATE_JOB_SELECT: 0,
    STATE_TOWN: 0,         STATE_TOWN_SUB: 0,        STATE_GUILD: 0,
    STATE_STAT_ALLOC: 0,   STATE_SHOP: 0,            STATE_HOME: 0,    STATE_REVIVE: 0,
    STATE_DUNGEON: 1,      STATE_DUNGEON_SKILL: 1,   STATE_DUNGEON_SHOP: 1,
    STATE_BATTLE_CMD: 2,   STATE_BATTLE_MSG: 2,      STATE_BATTLE_END: 2,
    STATE_BATTLE_NPC_CMD: 2, STATE_BATTLE_TARGET_PART: 2, STATE_BATTLE_TARGET: 2,
    STATE_BATTLE_SKILL: 2, STATE_LOG_VIEW: 2,
    STATE_ENDING: -1,
}
