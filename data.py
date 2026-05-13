import json
import random
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"


def _load_json(filename):
    with open(_DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


# ---- Jobs ----

class Job:
    def __init__(self, name, hp_die, mp_die, str_growth, def_growth, agi_growth, luk_growth=0.3):
        self.name = name
        self.hp_die = hp_die        # 1 to hp_die HP gained per level
        self.mp_die = mp_die        # 0 = no MP growth
        # probability of +1 per level (0.0-1.0)
        self.str_growth = str_growth
        self.def_growth = def_growth
        self.agi_growth = agi_growth
        self.luk_growth = luk_growth


def _build_jobs(raw):
    return {key: Job(**val) for key, val in raw.items()}


# ---- Items ----

class Item:
    def __init__(self, name, kind, value=0):
        self.name = name
        self.kind = kind   # "weapon" | "armor" | "consumable"
        self.value = value


class WeaponItem(Item):
    """Wiz風ハイブリッドダメージ: (dice_count × d(dice_sides)) + static_bonus + enchant_bonus"""

    def __init__(self, name, dice_count, dice_sides, static_bonus=0, enchant_bonus=0, value=0, attribute=None, weight_class="light"):
        super().__init__(name, "weapon", value)
        self.dice_count = dice_count
        self.dice_sides = dice_sides
        self.static_bonus = static_bonus
        self.enchant_bonus = enchant_bonus
        self.attribute = attribute
        self.weight_class = weight_class

    def roll_damage(self):
        dice = sum(random.randint(1, self.dice_sides)
                   for _ in range(self.dice_count))
        return dice + self.static_bonus + self.enchant_bonus

    def dmg_range(self):
        base = self.static_bonus + self.enchant_bonus
        return self.dice_count + base, self.dice_count * self.dice_sides + base

    def label(self):
        lo, hi = self.dmg_range()
        return f"{self.name} ({lo}-{hi})"

    def clone(self):
        return WeaponItem(self.name, self.dice_count, self.dice_sides,
                          self.static_bonus, self.enchant_bonus, self.value,
                          self.attribute, self.weight_class)


def _rarity_from_enchants(prefix=None, suffix=None, genesis=False):
    if genesis:
        return "genesis"
    count = (1 if prefix else 0) + (1 if suffix else 0)
    if count == 0:
        return "normal"
    strong_prefix = prefix and prefix.get("name") in ("Master",)
    if count == 2:
        return "legend" if strong_prefix else "epic"
    return "rare"


def _rarity_value(base_value, rarity):
    mult = {
        "normal": 1.0,
        "rare": 1.5,
        "epic": 2.5,
        "legend": 4.0,
        "genesis": 8.0,
    }.get(rarity, 1.0)
    return max(base_value, int(base_value * mult))


class EnchantedWeapon(WeaponItem):
    """WeaponItemにエンチャント（接頭辞・接尾辞）を付与した派生クラス。"""

    def __init__(self, base: WeaponItem, prefix=None, suffix=None, genesis=False):
        self.prefix = prefix   # dict | None
        self.suffix = suffix   # dict | None
        self.genesis = genesis
        self._base_name = getattr(base, "_base_name", base.name)
        self._base_dc = getattr(base, "_base_dc", base.dice_count)
        self._base_ds = getattr(base, "_base_ds", base.dice_sides)
        self._base_sb = getattr(base, "_base_sb", base.static_bonus)
        self._base_enchant_bonus = getattr(base, "_base_enchant_bonus", base.enchant_bonus)
        self._base_value = getattr(base, "_base_value", base.value)
        self._base_attribute = getattr(base, "_base_attribute", base.attribute)
        dc = self._base_dc + (prefix["dice_count_mod"] if prefix else 0)
        ds = self._base_ds + (prefix["dice_sides_mod"] if prefix else 0)
        sb = self._base_sb + (prefix["static_bonus_mod"] if prefix else 0)
        if genesis:
            dc = self._base_dc + 2
            ds = self._base_ds + 4
            sb = self._base_sb + 8
        rarity = _rarity_from_enchants(prefix, suffix, genesis)
        super().__init__(
            self._base_name, max(1, dc), max(1, ds), sb, self._base_enchant_bonus,
            _rarity_value(self._base_value, rarity),
            weight_class=getattr(base, "weight_class", "light"),
        )
        self.attribute = (suffix["attribute"] if suffix else None) or self._base_attribute

    @property
    def rarity(self):
        return _rarity_from_enchants(self.prefix, self.suffix, self.genesis)

    @property
    def is_cursed(self):
        return bool(self.prefix and self.prefix.get("dice_count_mod", 0) < 0)

    def label(self):
        if self.genesis:
            lo, hi = self.dmg_range()
            return f"Genesis {self._base_name} ({lo}-{hi})"
        parts = []
        if self.prefix:
            parts.append(self.prefix["name"])
        parts.append(self._base_name)
        if self.suffix:
            parts.append(f"+{self.suffix['name']}")
        lo, hi = self.dmg_range()
        return f"{''.join(parts) if self.prefix or self.suffix else self._base_name} ({lo}-{hi})"

    def clone(self):
        base = WeaponItem(self._base_name, self._base_dc, self._base_ds,
                          self._base_sb, self._base_enchant_bonus,
                          self._base_value, self._base_attribute,
                          self.weight_class)
        return EnchantedWeapon(base, self.prefix, self.suffix, self.genesis)


class ArmorItem(Item):
    def __init__(self, name, def_bonus, value=0, weight_class="light"):
        super().__init__(name, "armor", value)
        self.def_bonus = def_bonus
        self.attribute = None
        self.weight_class = weight_class

    def clone(self):
        return ArmorItem(self.name, self.def_bonus, self.value, self.weight_class)


class EnchantedArmor(ArmorItem):
    """ArmorItemに接頭辞（防御値変化）・接尾辞（属性耐性）を付与した派生クラス。"""

    def __init__(self, base: ArmorItem, prefix=None, suffix=None, genesis=False):
        self.prefix = prefix
        self.suffix = suffix
        self.genesis = genesis
        self._base_name = getattr(base, "_base_name", base.name)
        self._base_def = getattr(base, "_base_def", base.def_bonus)
        self._base_value = getattr(base, "_base_value", base.value)
        bonus_mod = prefix["def_bonus_mod"] if prefix else 0
        def_bonus = max(0, self._base_def + bonus_mod)
        if genesis:
            def_bonus = self._base_def + 8
        rarity = _rarity_from_enchants(prefix, suffix, genesis)
        super().__init__(
            self._base_name,
            def_bonus,
            _rarity_value(self._base_value, rarity),
            getattr(base, "weight_class", "light"),
        )
        self.attribute = suffix["attribute"] if suffix else None

    @property
    def rarity(self):
        return _rarity_from_enchants(self.prefix, self.suffix, self.genesis)

    def label(self):
        if self.genesis:
            return f"Genesis {self._base_name} (DEF+{self.def_bonus})"
        parts = []
        if self.prefix:
            parts.append(self.prefix["name"])
        parts.append(self._base_name)
        if self.suffix:
            parts.append(f"+{self.suffix['name']}")
        name = "".join(parts) if (self.prefix or self.suffix) else self._base_name
        return f"{name} (DEF+{self.def_bonus})"

    def clone(self):
        base = ArmorItem(self._base_name, self._base_def, self._base_value,
                         self.weight_class)
        return EnchantedArmor(base, self.prefix, self.suffix, self.genesis)


class ConsumableItem(Item):
    def __init__(self, name, hp_restore=0, mp_restore=0, value=0, cure_status=""):
        super().__init__(name, "consumable", value)
        self.hp_restore = hp_restore
        self.mp_restore = mp_restore
        self.cure_status = cure_status

    def clone(self):
        return ConsumableItem(self.name, self.hp_restore, self.mp_restore, self.value, self.cure_status)


class AccessoryItem(Item):
    def __init__(self, name, luk_bonus=0, mp_bonus=0, value=0):
        super().__init__(name, "accessory", value)
        self.luk_bonus = luk_bonus
        self.mp_bonus  = mp_bonus

    def label(self):
        parts = []
        if self.luk_bonus:
            parts.append(f"LUK+{self.luk_bonus}")
        if self.mp_bonus:
            parts.append(f"MP+{self.mp_bonus}")
        suffix = f" ({', '.join(parts)})" if parts else ""
        return f"{self.name}{suffix}"

    def clone(self):
        return AccessoryItem(self.name, self.luk_bonus, self.mp_bonus, self.value)


class GrimoireItem(ConsumableItem):
    """使用するとスキルを習得できる魔導書。"""

    def __init__(self, name, skill_name, mp_cost=5, effect_type="attack", power=10, value=0, is_utility=False):
        super().__init__(name, 0, 0, value)
        self.skill_name  = skill_name
        self.mp_cost     = mp_cost
        self.effect_type = effect_type
        self.power       = power
        self.is_utility  = is_utility

    def clone(self):
        return GrimoireItem(self.name, self.skill_name, self.mp_cost,
                            self.effect_type, self.power, self.value, self.is_utility)


def _build_item(raw):
    t = raw["type"]
    if t == "weapon":
        return WeaponItem(
            raw["name"], raw["dice_count"], raw["dice_sides"],
            raw.get("static_bonus", 0), 0, raw.get("value", 0),
            raw.get("attribute", None),
            raw.get("weight_class", "light"),
        )
    if t == "armor":
        return ArmorItem(raw["name"], raw["def_bonus"], raw.get("value", 0),
                         raw.get("weight_class", "light"))
    if t == "accessory":
        return AccessoryItem(raw["name"], raw.get("luk_bonus", 0),
                             raw.get("mp_bonus", 0), raw.get("value", 0))
    if t == "consumable":
        return ConsumableItem(
            raw["name"], raw.get("hp_restore", 0), raw.get("mp_restore", 0), raw.get("value", 0),
            raw.get("cure_status", "")
        )
    if t == "grimoire":
        return GrimoireItem(
            raw["name"], raw["skill_name"],
            raw.get("mp_cost", 5), raw.get("effect_type", "attack"),
            raw.get("power", 10), raw.get("value", 0),
            raw.get("is_utility", False),
        )
    raise ValueError(f"Unknown item type: {t}")


def _build_items(raw):
    return {key: _build_item(val) for key, val in raw.items()}


# ---- Enemy definitions ----

class EnemyDef:
    def __init__(self, name, hp, weapon, def_, exp_reward, gold_reward,
                 weaknesses=None, resistances=None, ai_type="normal",
                 telegraph_message="", inflict_status="", inflict_chance=0.0,
                 parts=None, sprite_u=0, sprite_v=0):
        self.name = name
        self.hp = hp
        self.weapon = weapon
        self.def_ = def_
        self.exp_reward = exp_reward
        self.gold_reward = gold_reward
        self.weaknesses        = weaknesses  or []
        self.resistances       = resistances or []
        self.ai_type           = ai_type
        self.telegraph_message = telegraph_message
        self.inflict_status    = inflict_status
        self.inflict_chance    = inflict_chance
        self.parts             = parts or []
        self.sprite_u          = sprite_u
        self.sprite_v          = sprite_v


def _build_enemies(raw):
    result = {}
    for key, val in raw.items():
        w = val["weapon"]
        weapon = WeaponItem(w["name"], w["dice_count"],
                            w["dice_sides"], w.get("static_bonus", 0))
        result[key] = EnemyDef(
            val["name"], val["hp"], weapon,
            val["def"], val["exp_reward"], val["gold_reward"],
            weaknesses=val.get("weaknesses", []),
            resistances=val.get("resistances", []),
            ai_type=val.get("ai_type", "normal"),
            telegraph_message=val.get("telegraph_message", ""),
            inflict_status=val.get("inflict_status", ""),
            inflict_chance=val.get("inflict_chance", 0.0),
            parts=val.get("parts", []),
            sprite_u=val.get("sprite_u", 0),
            sprite_v=val.get("sprite_v", 0),
        )
    return result


# ---- Load master data from JSON ----

JOBS = _build_jobs(_load_json("jobs.json"))
ITEM_CATALOG = _build_items(_load_json("items.json"))
ENEMY_CATALOG = _build_enemies(_load_json("enemies.json"))
_ENCHANTS = _load_json("enchants.json")


NPC_TYPES = {
    "slime":    {"name": "Slime",    "color": 11, "chase_range": 2, "wander_interval": 60, "enemy_key": "slime"},
    "bat":      {"name": "Bat",      "color": 6,  "chase_range": 3, "wander_interval": 30, "enemy_key": "bat"},
    "goblin":   {"name": "Goblin",   "color": 9,  "chase_range": 3, "wander_interval": 45, "enemy_key": "goblin"},
    "kobold":   {"name": "Kobold",   "color": 10, "chase_range": 3, "wander_interval": 35, "enemy_key": "kobold"},
    "ooze":     {"name": "Ooze",     "color": 11, "chase_range": 2, "wander_interval": 70, "enemy_key": "ooze"},
    "skeleton": {"name": "Skeleton", "color": 5,  "chase_range": 3, "wander_interval": 50, "enemy_key": "skeleton"},
    "wraith":   {"name": "Wraith",   "color": 12, "chase_range": 4, "wander_interval": 55, "enemy_key": "wraith"},
    "cultist":  {"name": "Cultist",  "color": 2,  "chase_range": 3, "wander_interval": 50, "enemy_key": "cultist"},
    "ice_hound": {"name": "Hound",   "color": 12, "chase_range": 4, "wander_interval": 35, "enemy_key": "ice_hound"},
    "golem":    {"name": "Golem",    "color": 6,  "chase_range": 3, "wander_interval": 70, "enemy_key": "golem"},
    "wyvern":   {"name": "Wyvern",   "color": 8,  "chase_range": 5, "wander_interval": 35, "enemy_key": "wyvern"},
    "dark_knight": {"name": "Knight", "color": 5, "chase_range": 4, "wander_interval": 50, "enemy_key": "dark_knight"},
    "lich":     {"name": "Lich",     "color": 13, "chase_range": 4, "wander_interval": 60, "enemy_key": "lich"},
    "porter":   {"name": "Porter",   "color": 10, "chase_range": 2, "wander_interval": 65, "enemy_key": "goblin",
                 "recruitable": True, "job_key": "porter", "personality": "normal"},
    "mercenary": {"name": "Merc",    "color": 15, "chase_range": 2, "wander_interval": 55, "enemy_key": "skeleton",
                  "recruitable": True, "job_key": "warrior", "personality": "reckless"},
}

# 三すくみ属性相性: fire > ice > poison > fire
ATTR_AFFINITY = {"fire": "ice", "ice": "poison", "poison": "fire"}

MAX_SKILLS = 4


class Skill:
    """プレイヤーが魔導書から習得できるアクティブスキル。"""

    def __init__(self, name, mp_cost=5, effect_type="attack", power=10, is_utility=False):
        self.name        = name
        self.mp_cost     = mp_cost
        self.effect_type = effect_type  # "attack" | "heal" | "teleport"
        self.power       = power
        self.is_utility  = is_utility


# Job-specific starting skills granted on character creation or job change.
# effect_type: "encourage" | "provoke" | "quick_strike" | "mana_bolt" (handled in App._execute_active_skill)
JOB_SKILLS: dict = {
    "porter":  Skill("Encourage",     mp_cost=4, effect_type="encourage",    power=10),
    "warrior": Skill("Provoke",       mp_cost=3, effect_type="provoke",      power=2),
    "thief":   Skill("Quick Strike",  mp_cost=4, effect_type="quick_strike", power=0),
    "mage":    Skill("Mana Bolt",     mp_cost=5, effect_type="mana_bolt",    power=3),
}


def make_enchanted_armor(base_key: str) -> EnchantedArmor:
    """ベース防具にウェイト抽選でエンチャントを付与したEnchantedArmorを返す。"""
    base = ITEM_CATALOG[base_key]
    if random.random() < 0.005:
        return EnchantedArmor(base, genesis=True)

    def _pick(pool: dict):
        keys = list(pool.keys())
        weights = [pool[k]["weight"] for k in keys]
        total = sum(weights)
        r = random.randint(0, total * 2 - 1)
        if r >= total:
            return None
        acc = 0
        for k, w in zip(keys, weights):
            acc += w
            if r < acc:
                return pool[k]
        return None

    prefix = _pick(_ENCHANTS["armor_prefixes"])
    suffix = _pick(_ENCHANTS["armor_suffixes"])
    return EnchantedArmor(base, prefix, suffix)


def make_enchanted_weapon(base_key: str) -> EnchantedWeapon:
    """ベース武器にウェイト抽選でエンチャントを付与したEnchantedWeaponを返す。
    接頭辞・接尾辞ともに付与なし（Common）になることもある。"""
    base = ITEM_CATALOG[base_key]
    if random.random() < 0.005:
        return EnchantedWeapon(base, genesis=True)

    def _pick(pool: dict):
        keys = list(pool.keys())
        weights = [pool[k]["weight"] for k in keys]
        total = sum(weights)
        # 同じウェイト合計分だけ「なし」の枠も用意して付与確率を50%に
        r = random.randint(0, total * 2 - 1)
        if r >= total:
            return None
        acc = 0
        for k, w in zip(keys, weights):
            acc += w
            if r < acc:
                return pool[k]
        return None

    prefix = _pick(_ENCHANTS["prefixes"])
    suffix = _pick(_ENCHANTS["suffixes"])
    return EnchantedWeapon(base, prefix, suffix)


# ---- Grave (lost item recovery) ----

class Grave:
    def __init__(self, floor, x, y, item):
        self.floor = floor
        self.x = x
        self.y = y
        self.item = item


# ---- Status (character stats sheet) ----

class Status:
    def __init__(self, job_key="warrior", name="Hero"):
        job = JOBS[job_key]
        self.name = name
        self.job_key = job_key
        self.job = job
        self.level = 1
        self.exp = 0

        self.max_hp = job.hp_die * 3
        self.max_mp = job.mp_die * 2 if job.mp_die > 0 else 0
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.str_ = 5
        self.def_ = 2
        self.agi = 3
        self.luk = 3

        self.weapon    = ITEM_CATALOG["old_dagger"]
        self.armor     = None
        self.accessory = None
        self.weaknesses   = []
        self._resistances = []
        self.personality  = "normal"  # "normal" | "reckless" | "cowardly" | "selfish"
        self.skills       = []        # max MAX_SKILLS slots
        self.mag          = 2
        self.bonus_points = 0
        self.status_effects = {"poison": 0, "stun": 0}

    @property
    def resistances(self) -> list:
        """装備中の防具が持つ attribute を耐性リストに自動的に含む。"""
        base = list(self._resistances)
        if self.armor and getattr(self.armor, "attribute", None):
            if self.armor.attribute not in base:
                base.append(self.armor.attribute)
        return base

    @resistances.setter
    def resistances(self, value: list):
        self._resistances = value

    @property
    def total_luk(self):
        return self.luk + (self.accessory.luk_bonus if self.accessory else 0)

    @property
    def total_max_mp(self):
        return self.max_mp + (self.accessory.mp_bonus if self.accessory else 0)

    @property
    def exp_to_next(self):
        return 100 * self.level

    @property
    def total_def(self):
        bonus = self.armor.def_bonus if self.armor else 0
        return self.def_ + bonus

    def gain_exp(self, amount):
        self.exp += amount
        level_ups = []
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            level_ups.append(self._do_level_up())
        return level_ups

    def _do_level_up(self):
        job = self.job
        hp_gain  = random.randint(1, job.hp_die)
        mp_gain  = random.randint(1, job.mp_die) if job.mp_die > 0 else 0
        str_gain = 1 if random.random() < job.str_growth else 0
        def_gain = 1 if random.random() < job.def_growth else 0
        agi_gain = 1 if random.random() < job.agi_growth else 0
        luk_gain = 1 if random.random() < job.luk_growth else 0
        self.level  += 1
        self.max_hp += hp_gain
        self.max_mp += mp_gain
        self.str_ += str_gain
        self.def_ += def_gain
        self.agi  += agi_gain
        self.luk  += luk_gain
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.bonus_points += 3
        return {"hp": hp_gain, "mp": mp_gain, "str": str_gain,
                "def": def_gain, "agi": agi_gain, "luk": luk_gain}


class NPCMember(Status):
    """パーティに加わる臨時NPC。性格（癖）に基づくAI行動を持つ。"""

    PERSONALITIES = ("normal", "reckless", "cowardly", "selfish")

    def __init__(self, job_key="warrior", name="NPC", personality="normal"):
        super().__init__(job_key, name)
        self.personality = personality if personality in self.PERSONALITIES else "normal"
        self.inventory = []
        self.is_unique = False  # True: 固有NPC（昇格済み、手動操作可能）


class Party:
    """プレイヤー1名 + 臨時NPC最大3名を管理するパーティクラス。"""

    MAX_SIZE = 4

    def __init__(self, player):
        self.members = [player]

    def add(self, member) -> bool:
        if len(self.members) >= self.MAX_SIZE:
            return False
        self.members.append(member)
        return True

    @property
    def is_wiped_out(self) -> bool:
        return all(m.hp <= 0 for m in self.members)

    @property
    def alive(self) -> list:
        return [m for m in self.members if m.hp > 0]

    @property
    def fallen(self) -> list:
        return [m for m in self.members if m.hp <= 0]
