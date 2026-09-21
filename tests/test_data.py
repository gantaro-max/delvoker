import random

from data import (
    ATTR_AFFINITY,
    ENEMY_CATALOG,
    ITEM_CATALOG,
    JOBS,
    ArmorItem,
    NPCMember,
    Party,
    Status,
    make_enchanted_armor,
    make_enchanted_weapon,
)


def is_ascii(value):
    return value.isascii()


def test_catalogs_are_populated_and_names_are_ascii():
    assert JOBS
    assert ITEM_CATALOG
    assert ENEMY_CATALOG
    assert all(is_ascii(item.name) for item in ITEM_CATALOG.values())
    assert all(is_ascii(enemy.name) for enemy in ENEMY_CATALOG.values())


def test_each_job_creates_at_full_health():
    for job_key in JOBS:
        member = Status(job_key)
        assert member.hp == member.max_hp


def test_enemy_attributes_and_affinity_form_the_expected_cycle():
    allowed = {"fire", "ice", "poison", "holy"}
    for enemy in ENEMY_CATALOG.values():
        assert set(enemy.weaknesses) <= allowed
        assert set(enemy.resistances) <= allowed

    assert set(ATTR_AFFINITY) == {"fire", "ice", "poison"}
    for attribute in ATTR_AFFINITY:
        assert ATTR_AFFINITY[ATTR_AFFINITY[attribute]] in ATTR_AFFINITY
    assert ATTR_AFFINITY[ATTR_AFFINITY[ATTR_AFFINITY["fire"]]] == "fire"


def test_experience_can_level_up_multiple_times_and_restores_hp():
    random.seed(1)
    member = Status("warrior")
    member.hp = 1
    gains = member.gain_exp(300)

    assert len(gains) == 2
    assert member.level == 3
    assert member.bonus_points == 6
    assert member.hp == member.max_hp
    assert member.exp == 0


def test_equipment_affects_defense_and_resistances():
    member = Status("warrior")
    armor = ArmorItem("Test Armor", 4)
    armor.attribute = "fire"
    member.armor = armor

    assert member.total_def == member.def_ + 4
    assert "fire" in member.resistances


def test_party_capacity_and_wipe_state():
    player = Status("porter")
    party = Party(player)
    assert party.MAX_SIZE == 4
    while len(party.members) < party.MAX_SIZE:
        assert party.add(Status("warrior"))
    assert not party.add(Status("warrior"))
    assert not party.is_wiped_out
    for member in party.members:
        member.hp = 0
    assert party.is_wiped_out


def test_unknown_npc_personality_falls_back_to_normal():
    assert NPCMember(personality="unknown").personality == "normal"


def test_generated_enchantment_labels_are_ascii():
    for seed in range(20):
        random.seed(seed)
        assert make_enchanted_weapon("short_sword").label().isascii()
        assert make_enchanted_armor("leather_armor").label().isascii()
