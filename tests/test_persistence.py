from types import SimpleNamespace

from data import (
    AccessoryItem,
    ArmorItem,
    ConsumableItem,
    EnchantedArmor,
    EnchantedWeapon,
    GrimoireItem,
    NPCMember,
    Skill,
    WeaponItem,
)
from systems.persistence import (
    deserialize_item,
    deserialize_npc_member,
    load_game,
    save_game,
    serialize_item,
    serialize_member,
)


def assert_item_round_trip(item):
    restored = deserialize_item(serialize_item(item))
    assert type(restored) is type(item)
    assert restored.name == item.name
    assert restored.value == item.value
    if hasattr(item, "label"):
        assert restored.label() == item.label()


def test_every_item_subclass_round_trips():
    weapon = WeaponItem("Blade", 2, 6, 1, 2, 30, "fire", "medium")
    armor = ArmorItem("Mail", 3, 20, "heavy")
    prefix = {"name": "Fine", "dice_count_mod": 1, "dice_sides_mod": 0, "static_bonus_mod": 2}
    suffix = {"name": "Flame", "attribute": "fire"}
    armor_prefix = {"name": "Guard", "def_bonus_mod": 2}
    items = [
        weapon,
        armor,
        ConsumableItem("Potion", 10, 2, 5, "poison"),
        AccessoryItem("Charm", 2, 3, 7),
        GrimoireItem("Tome", "Heal", 4, "heal", 12, 15, True),
        EnchantedWeapon(weapon, prefix, suffix),
        EnchantedArmor(armor, armor_prefix, suffix),
    ]
    for item in items:
        assert_item_round_trip(item)


def test_old_consumable_payload_without_kind_is_supported():
    item = deserialize_item({"name": "Herb", "hp_restore": 5, "value": 3})
    assert isinstance(item, ConsumableItem)
    assert item.name == "Herb"
    assert item.hp_restore == 5


def test_npc_round_trip_preserves_stats_equipment_and_skills():
    member = NPCMember("mage", "Mira", "reckless")
    member.level = 4
    member.max_hp = 50
    member.hp = 31
    member.is_unique = True
    member.weapon = WeaponItem("Staff", 1, 8)
    member.armor = ArmorItem("Robe", 2)
    member.accessory = AccessoryItem("Ring", 1, 2)
    member.skills = [Skill("Bolt", 3, "attack", 8)]

    restored = deserialize_npc_member(serialize_member(member))
    assert restored.level == 4
    assert restored.max_hp == 50
    assert restored.hp == 31
    assert restored.is_unique
    assert restored.weapon.name == "Staff"
    assert restored.armor.name == "Robe"
    assert restored.accessory.name == "Ring"
    assert restored.skills[0].name == "Bolt"


def test_loaded_npc_health_is_clamped_to_maximum():
    member = deserialize_npc_member({"name": "NPC", "max_hp": 10, "hp": 99})
    assert member.hp == 10


def test_save_and_load_round_trip_is_ascii(tmp_path):
    path = tmp_path / "save.json"
    player = SimpleNamespace(
        name="Hero",
        gold=42,
        warehouse=[ConsumableItem("Potion", hp_restore=10, value=5)],
        warehouse_max=12,
        perm_stats={"str": 1, "def": 2, "mag": 3},
    )
    npc = NPCMember("warrior", "Gard", "normal")
    save_game(player, ["porter", "warrior"], True, {"slime": 2}, [npc], path)

    assert path.read_text(encoding="ascii").isascii()
    saved = load_game(path)
    assert saved["player_name"] == "Hero"
    assert saved["gold"] == 42
    assert saved["warehouse_max"] == 12
    assert saved["perm_stats"] == player.perm_stats
    assert saved["unlocked_jobs"] == ["porter", "warrior"]
    assert saved["game_cleared"] is True
    assert saved["bestiary"] == {"slime": 2}
    assert deserialize_item(saved["warehouse"][0]).name == "Potion"
    assert deserialize_npc_member(saved["party_npcs"][0]).name == "Gard"


def test_missing_or_invalid_save_returns_empty_data(tmp_path):
    missing = tmp_path / "missing.json"
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not json", encoding="ascii")
    assert load_game(missing) == {}
    assert load_game(invalid) == {}
