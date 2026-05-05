import random


# ---- Jobs ----

class Job:
    def __init__(self, name, hp_die, mp_die, str_growth, def_growth, agi_growth):
        self.name = name
        self.hp_die = hp_die        # 1 to hp_die HP gained per level
        self.mp_die = mp_die        # 0 = no MP growth
        self.str_growth = str_growth  # probability of +1 STR per level (0.0-1.0)
        self.def_growth = def_growth
        self.agi_growth = agi_growth


JOBS = {
    "warrior": Job("Warrior", hp_die=12, mp_die=0, str_growth=0.8, def_growth=0.6, agi_growth=0.3),
    "mage":    Job("Mage",    hp_die=4,  mp_die=8, str_growth=0.2, def_growth=0.1, agi_growth=0.5),
    "cleric":  Job("Cleric",  hp_die=7,  mp_die=5, str_growth=0.3, def_growth=0.4, agi_growth=0.4),
}


# ---- Items ----

class Item:
    def __init__(self, name, kind, value=0):
        self.name = name
        self.kind = kind   # "weapon" | "armor" | "consumable"
        self.value = value


class WeaponItem(Item):
    """Wiz風ハイブリッドダメージ: (dice_count × d(dice_sides)) + static_bonus + enchant_bonus"""
    def __init__(self, name, dice_count, dice_sides, static_bonus=0, enchant_bonus=0, value=0):
        super().__init__(name, "weapon", value)
        self.dice_count = dice_count
        self.dice_sides = dice_sides
        self.static_bonus = static_bonus
        self.enchant_bonus = enchant_bonus

    def roll_damage(self):
        dice = sum(random.randint(1, self.dice_sides) for _ in range(self.dice_count))
        return dice + self.static_bonus + self.enchant_bonus

    def dmg_range(self):
        base = self.static_bonus + self.enchant_bonus
        return self.dice_count + base, self.dice_count * self.dice_sides + base

    def label(self):
        lo, hi = self.dmg_range()
        return f"{self.name} ({lo}-{hi})"


class ArmorItem(Item):
    def __init__(self, name, def_bonus, value=0):
        super().__init__(name, "armor", value)
        self.def_bonus = def_bonus


class ConsumableItem(Item):
    def __init__(self, name, hp_restore=0, mp_restore=0, value=0):
        super().__init__(name, "consumable", value)
        self.hp_restore = hp_restore
        self.mp_restore = mp_restore


# ---- Item catalog ----

ITEM_CATALOG = {
    "old_dagger":    WeaponItem("Old Dagger",   1, 6,          value=10),
    "short_sword":   WeaponItem("Short Sword",  1, 8,  1,      value=50),
    "long_sword":    WeaponItem("Long Sword",   1, 10, 2,      value=150),
    "staff":         WeaponItem("Staff",        1, 4,          value=20),
    "leather_armor": ArmorItem("Leather Armor", def_bonus=2,   value=30),
    "chain_mail":    ArmorItem("Chain Mail",    def_bonus=4,   value=100),
    "herb":          ConsumableItem("Herb",     hp_restore=10, value=15),
    "potion":        ConsumableItem("Potion",   hp_restore=30, value=50),
    "ether":         ConsumableItem("Ether",    mp_restore=15, value=60),
}


# ---- Enemy definitions ----

class EnemyDef:
    def __init__(self, name, hp, weapon, def_, exp_reward, gold_reward):
        self.name = name
        self.hp = hp
        self.weapon = weapon
        self.def_ = def_
        self.exp_reward = exp_reward
        self.gold_reward = gold_reward


ENEMY_CATALOG = {
    "slime":    EnemyDef("Slime",    15, WeaponItem("Slime Body",  1, 4),     1, 10,  5),
    "bat":      EnemyDef("Bat",      10, WeaponItem("Bite",        1, 3),     0,  8,  3),
    "skeleton": EnemyDef("Skeleton", 25, WeaponItem("Bone Club",   1, 6),     2, 20, 15),
    "goblin":   EnemyDef("Goblin",   20, WeaponItem("Rusty Sword", 1, 6, 1), 1, 15, 10),
}


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
