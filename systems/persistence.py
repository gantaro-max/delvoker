import json
from data import (
    WeaponItem, EnchantedWeapon, ArmorItem, EnchantedArmor,
    GrimoireItem, ConsumableItem, AccessoryItem,
)
from constants import SAVE_FILE


def serialize_item(item):
    if isinstance(item, EnchantedWeapon):
        prefix = item.prefix
        return {"kind": "enchanted_weapon",
                "base_name": item._base_name,
                "base_dc": getattr(item, "_base_dc", item.dice_count - (prefix["dice_count_mod"] if prefix else 0)),
                "base_ds": getattr(item, "_base_ds", item.dice_sides - (prefix["dice_sides_mod"] if prefix else 0)),
                "base_sb": getattr(item, "_base_sb", item.static_bonus - (prefix["static_bonus_mod"] if prefix else 0)),
                "enchant_bonus": getattr(item, "_base_enchant_bonus", item.enchant_bonus),
                "value": getattr(item, "_base_value", item.value),
                "attribute": getattr(item, "_base_attribute", item.attribute),
                "weight_class": getattr(item, "weight_class", "light"),
                "prefix": prefix, "suffix": item.suffix,
                "genesis": getattr(item, "genesis", False)}
    if isinstance(item, WeaponItem):
        return {"kind": "weapon",
                "name": item.name, "dice_count": item.dice_count,
                "dice_sides": item.dice_sides, "static_bonus": item.static_bonus,
                "enchant_bonus": item.enchant_bonus, "value": item.value,
                "attribute": item.attribute,
                "weight_class": getattr(item, "weight_class", "light")}
    if isinstance(item, EnchantedArmor):
        prefix = item.prefix
        return {"kind": "enchanted_armor",
                "base_name": item._base_name,
                "base_def": getattr(item, "_base_def", item.def_bonus - (prefix["def_bonus_mod"] if prefix else 0)),
                "value": getattr(item, "_base_value", item.value),
                "weight_class": getattr(item, "weight_class", "light"),
                "prefix": prefix, "suffix": item.suffix,
                "genesis": getattr(item, "genesis", False)}
    if isinstance(item, ArmorItem):
        return {"kind": "armor",
                "name": item.name, "def_bonus": item.def_bonus,
                "value": item.value,
                "weight_class": getattr(item, "weight_class", "light")}
    if isinstance(item, GrimoireItem):
        return {"kind": "grimoire",
                "name": item.name, "skill_name": item.skill_name,
                "mp_cost": item.mp_cost, "effect_type": item.effect_type,
                "power": item.power, "value": item.value, "is_utility": item.is_utility}
    if isinstance(item, AccessoryItem):
        return {"kind": "accessory",
                "name": item.name, "luk_bonus": item.luk_bonus,
                "mp_bonus": item.mp_bonus, "value": item.value}
    return {"kind": "consumable",
            "name": item.name, "hp_restore": getattr(item, "hp_restore", 0),
            "mp_restore": getattr(item, "mp_restore", 0), "value": item.value,
            "cure_status": getattr(item, "cure_status", "")}


def deserialize_item(d):
    k = d.get("kind", "consumable")
    if k == "enchanted_weapon":
        base = WeaponItem(d["base_name"], d["base_dc"], d["base_ds"],
                          d.get("base_sb", 0), d.get("enchant_bonus", 0),
                          d.get("value", 0), d.get("attribute"),
                          d.get("weight_class", "light"))
        return EnchantedWeapon(base, d.get("prefix"), d.get("suffix"),
                               d.get("genesis", False))
    if k == "weapon":
        return WeaponItem(d["name"], d["dice_count"], d["dice_sides"],
                          d.get("static_bonus", 0), d.get("enchant_bonus", 0),
                          d.get("value", 0), d.get("attribute"),
                          d.get("weight_class", "light"))
    if k == "enchanted_armor":
        base = ArmorItem(d["base_name"], d["base_def"], d.get("value", 0),
                         d.get("weight_class", "light"))
        return EnchantedArmor(base, d.get("prefix"), d.get("suffix"),
                              d.get("genesis", False))
    if k == "armor":
        return ArmorItem(d["name"], d["def_bonus"], d.get("value", 0),
                         d.get("weight_class", "light"))
    if k == "grimoire":
        return GrimoireItem(d["name"], d["skill_name"], d.get("mp_cost", 5),
                            d.get("effect_type", "attack"), d.get("power", 10),
                            d.get("value", 0), d.get("is_utility", False))
    if k == "accessory":
        return AccessoryItem(d["name"], d.get("luk_bonus", 0),
                             d.get("mp_bonus", 0), d.get("value", 0))
    return ConsumableItem(d["name"], d.get("hp_restore", 0), d.get("mp_restore", 0),
                          d.get("value", 0), d.get("cure_status", ""))


def save_game(player, unlocked_jobs, game_cleared, bestiary=None, filepath=SAVE_FILE):
    data = {
        "gold": player.gold,
        "warehouse": [serialize_item(it) for it in player.warehouse],
        "warehouse_max": player.warehouse_max,
        "perm_stats": dict(player.perm_stats),
        "unlocked_jobs": list(unlocked_jobs),
        "game_cleared": game_cleared,
        "bestiary": bestiary or {},
    }
    with open(filepath, "w", encoding="ascii") as f:
        json.dump(data, f, ensure_ascii=True)


def load_game(filepath=SAVE_FILE):
    """Returns a dict of saved fields, or an empty dict on failure."""
    try:
        with open(filepath, encoding="ascii") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}
