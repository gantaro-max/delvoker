import json
import random
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"


def _load_json(filename):
    with open(_DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


# ---- Jobs ----

class Job:
    def __init__(self, name, hp_die, mp_die, str_growth, def_growth, agi_growth):
        self.name = name
        self.hp_die = hp_die        # 1 to hp_die HP gained per level
        self.mp_die = mp_die        # 0 = no MP growth
        # probability of +1 STR per level (0.0-1.0)
        self.str_growth = str_growth
        self.def_growth = def_growth
        self.agi_growth = agi_growth


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

    def __init__(self, name, dice_count, dice_sides, static_bonus=0, enchant_bonus=0, value=0, attribute=None):
        super().__init__(name, "weapon", value)
        self.dice_count = dice_count
        self.dice_sides = dice_sides
        self.static_bonus = static_bonus
        self.enchant_bonus = enchant_bonus
        self.attribute = attribute

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
                          self.static_bonus, self.enchant_bonus, self.value, self.attribute)


class EnchantedWeapon(WeaponItem):
    """WeaponItemにエンチャント（接頭辞・接尾辞）を付与した派生クラス。"""

    def __init__(self, base: WeaponItem, prefix=None, suffix=None):
        super().__init__(
            base.name,
            base.dice_count + (prefix["dice_count_mod"] if prefix else 0),
            base.dice_sides + (prefix["dice_sides_mod"] if prefix else 0),
            base.static_bonus + (prefix["static_bonus_mod"] if prefix else 0),
            base.enchant_bonus,
            base.value,
        )
        self.prefix = prefix   # dict | None
        self.suffix = suffix   # dict | None
        self.attribute = (suffix["attribute"] if suffix else None) or base.attribute
        self._base_name = base.name

    @property
    def rarity(self):
        cursed = self.prefix and self.prefix.get("dice_count_mod", 0) < 0
        if cursed:
            return "cursed"
        both = self.prefix and self.suffix
        if both:
            return "rare"
        if self.prefix or self.suffix:
            return "magic"
        return "common"

    def label(self):
        parts = []
        if self.prefix:
            parts.append(self.prefix["name"])
        parts.append(self._base_name)
        if self.suffix:
            parts.append(f"+{self.suffix['name']}")
        lo, hi = self.dmg_range()
        return f"{''.join(parts) if self.prefix or self.suffix else self._base_name} ({lo}-{hi})"

    def clone(self):
        base = WeaponItem(self._base_name, self.dice_count, self.dice_sides,
                          self.static_bonus, self.enchant_bonus, self.value)
        return EnchantedWeapon(base, self.prefix, self.suffix)


class ArmorItem(Item):
    def __init__(self, name, def_bonus, value=0):
        super().__init__(name, "armor", value)
        self.def_bonus = def_bonus
        self.attribute = None

    def clone(self):
        return ArmorItem(self.name, self.def_bonus, self.value)


class EnchantedArmor(ArmorItem):
    """ArmorItemに接頭辞（防御値変化）・接尾辞（属性耐性）を付与した派生クラス。"""

    def __init__(self, base: ArmorItem, prefix=None, suffix=None):
        bonus_mod = prefix["def_bonus_mod"] if prefix else 0
        super().__init__(
            base.name,
            max(0, base.def_bonus + bonus_mod),
            base.value,
        )
        self.prefix = prefix
        self.suffix = suffix
        self.attribute = suffix["attribute"] if suffix else None
        self._base_name = base.name

    @property
    def rarity(self):
        if self.prefix or self.suffix:
            return "magic"
        return "common"

    def label(self):
        parts = []
        if self.prefix:
            parts.append(self.prefix["name"])
        parts.append(self._base_name)
        if self.suffix:
            parts.append(f"+{self.suffix['name']}")
        name = "".join(parts) if (self.prefix or self.suffix) else self._base_name
        return f"{name} (DEF+{self.def_bonus})"

    def clone(self):
        base = ArmorItem(self._base_name, self.def_bonus, self.value)
        return EnchantedArmor(base, self.prefix, self.suffix)


class ConsumableItem(Item):
    def __init__(self, name, hp_restore=0, mp_restore=0, value=0):
        super().__init__(name, "consumable", value)
        self.hp_restore = hp_restore
        self.mp_restore = mp_restore

    def clone(self):
        return ConsumableItem(self.name, self.hp_restore, self.mp_restore, self.value)


class GrimoireItem(ConsumableItem):
    """使用するとスキルを習得できる魔導書。"""

    def __init__(self, name, skill_name, mp_cost=5, effect_type="attack", power=10, value=0):
        super().__init__(name, 0, 0, value)
        self.skill_name  = skill_name
        self.mp_cost     = mp_cost
        self.effect_type = effect_type
        self.power       = power

    def clone(self):
        return GrimoireItem(self.name, self.skill_name, self.mp_cost,
                            self.effect_type, self.power, self.value)


def _build_item(raw):
    t = raw["type"]
    if t == "weapon":
        return WeaponItem(
            raw["name"], raw["dice_count"], raw["dice_sides"],
            raw.get("static_bonus", 0), 0, raw.get("value", 0),
            raw.get("attribute", None),
        )
    if t == "armor":
        return ArmorItem(raw["name"], raw["def_bonus"], raw.get("value", 0))
    if t == "consumable":
        return ConsumableItem(
            raw["name"], raw.get("hp_restore", 0), raw.get("mp_restore", 0), raw.get("value", 0)
        )
    if t == "grimoire":
        return GrimoireItem(
            raw["name"], raw["skill_name"],
            raw.get("mp_cost", 5), raw.get("effect_type", "attack"),
            raw.get("power", 10), raw.get("value", 0),
        )
    raise ValueError(f"Unknown item type: {t}")


def _build_items(raw):
    return {key: _build_item(val) for key, val in raw.items()}


# ---- Enemy definitions ----

class EnemyDef:
    def __init__(self, name, hp, weapon, def_, exp_reward, gold_reward, weaknesses=None, resistances=None):
        self.name = name
        self.hp = hp
        self.weapon = weapon
        self.def_ = def_
        self.exp_reward = exp_reward
        self.gold_reward = gold_reward
        self.weaknesses  = weaknesses  or []
        self.resistances = resistances or []


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
        )
    return result


# ---- Load master data from JSON ----

JOBS = _build_jobs(_load_json("jobs.json"))
ITEM_CATALOG = _build_items(_load_json("items.json"))
ENEMY_CATALOG = _build_enemies(_load_json("enemies.json"))
_ENCHANTS = _load_json("enchants.json")


NPC_TYPES = {
    "slime":  {"name": "Slime",  "color": 11, "chase_range": 2, "wander_interval": 60, "enemy_key": "slime"},
    "goblin": {"name": "Goblin", "color": 9,  "chase_range": 3, "wander_interval": 45, "enemy_key": "goblin"},
}

# 三すくみ属性相性: fire > ice > poison > fire
ATTR_AFFINITY = {"fire": "ice", "ice": "poison", "poison": "fire"}

MAX_SKILLS = 4


class Skill:
    """プレイヤーが魔導書から習得できるアクティブスキル。"""

    def __init__(self, name, mp_cost=5, effect_type="attack", power=10):
        self.name        = name
        self.mp_cost     = mp_cost
        self.effect_type = effect_type  # "attack" | "heal"
        self.power       = power


def make_enchanted_armor(base_key: str) -> EnchantedArmor:
    """ベース防具にウェイト抽選でエンチャントを付与したEnchantedArmorを返す。"""
    base = ITEM_CATALOG[base_key]

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


# ---- Status (character stats sheet) ----

class Status:
    def __init__(self, job_key="warrior", name="Hero"):
        job = JOBS[job_key]
        self.name = name
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

        self.weapon = ITEM_CATALOG["old_dagger"]
        self.armor = None
        self.weaknesses   = []
        self._resistances = []
        self.personality  = "normal"  # "normal" | "reckless" | "cowardly" | "selfish"
        self.skills       = []        # max MAX_SKILLS slots

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
        hp_gain = random.randint(1, job.hp_die)
        mp_gain = random.randint(1, job.mp_die) if job.mp_die > 0 else 0
        str_gain = 1 if random.random() < job.str_growth else 0
        def_gain = 1 if random.random() < job.def_growth else 0
        agi_gain = 1 if random.random() < job.agi_growth else 0
        self.level += 1
        self.max_hp += hp_gain
        self.max_mp += mp_gain
        self.str_ += str_gain
        self.def_ += def_gain
        self.agi += agi_gain
        self.hp = self.max_hp
        self.mp = self.max_mp
        return {"hp": hp_gain, "mp": mp_gain, "str": str_gain,
                "def": def_gain, "agi": agi_gain}


class NPCMember(Status):
    """パーティに加わる臨時NPC。性格（癖）に基づくAI行動を持つ。"""

    PERSONALITIES = ("normal", "reckless", "cowardly", "selfish")

    def __init__(self, job_key="warrior", name="NPC", personality="normal"):
        super().__init__(job_key, name)
        self.personality = personality if personality in self.PERSONALITIES else "normal"
        self.inventory = []
        self.is_unique = False  # True: 固有NPC（昇格済み、手動操作可能）


class Party:
    """プレイヤー1名 + 臨時NPC最大2名を管理するパーティクラス。"""

    MAX_SIZE = 3

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
