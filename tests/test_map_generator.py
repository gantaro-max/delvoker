from collections import deque
import random

from constants import (
    TILE_CHEST,
    TILE_LOCKED_DOOR,
    TILE_MERCHANT,
    TILE_STAIRS,
    TILE_WALL,
)
import logic.map_generator as map_generator
from logic.map_generator import Map


def reachable_tiles(dungeon_map, blocked=(TILE_WALL,)):
    start = (dungeon_map.start_x, dungeon_map.start_y)
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < dungeon_map.width and 0 <= ny < dungeon_map.height):
                continue
            if dungeon_map.tiles[ny][nx] in blocked or (nx, ny) in seen:
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))
    return seen


def tiles_of(dungeon_map, tile):
    return [
        (x, y)
        for y, row in enumerate(dungeon_map.tiles)
        for x, value in enumerate(row)
        if value == tile
    ]


def test_generated_maps_preserve_floor_invariants():
    for seed in range(20):
        random.seed(seed)
        dungeon_map = Map.generate_random(current_floor=1)

        assert all(tile == TILE_WALL for tile in dungeon_map.tiles[0])
        assert all(tile == TILE_WALL for tile in dungeon_map.tiles[-1])
        assert all(row[0] == TILE_WALL and row[-1] == TILE_WALL for row in dungeon_map.tiles)
        assert dungeon_map.tiles[dungeon_map.start_y][dungeon_map.start_x] != TILE_WALL
        assert len(tiles_of(dungeon_map, TILE_STAIRS)) == 1

        reachable = reachable_tiles(dungeon_map)
        assert tiles_of(dungeon_map, TILE_STAIRS)[0] in reachable
        assert not tiles_of(dungeon_map, TILE_LOCKED_DOOR)
        assert not tiles_of(dungeon_map, TILE_MERCHANT)


def test_key_chest_is_reachable_when_a_locked_door_is_generated():
    found_door = False
    for seed in [*range(100), 189, 1026, 1088]:
        random.seed(seed)
        dungeon_map = Map.generate_random(current_floor=3)
        assert len(tiles_of(dungeon_map, TILE_STAIRS)) == 1
        if not tiles_of(dungeon_map, TILE_LOCKED_DOOR):
            assert dungeon_map.key_chest_pos is None
            continue
        found_door = True
        assert dungeon_map.key_chest_pos is not None
        x, y = dungeon_map.key_chest_pos
        assert dungeon_map.tiles[y][x] == TILE_CHEST
        assert (x, y) in reachable_tiles(
            dungeon_map, blocked=(TILE_WALL, TILE_LOCKED_DOOR)
        )
    assert found_door


def test_chest_placement_does_not_overwrite_stairs():
    random.seed(15)
    dungeon_map = Map.generate_random(width=8, height=9, current_floor=3)

    assert len(tiles_of(dungeon_map, TILE_STAIRS)) == 1


def test_locked_doors_are_removed_if_no_key_chest_position(monkeypatch):
    monkeypatch.setattr(
        map_generator, "_reachable",
        lambda tiles, width, height, start, blocked: {start},
    )
    random.seed(189)
    dungeon_map = Map.generate_random(current_floor=3)

    assert dungeon_map.key_chest_pos is None
    assert not tiles_of(dungeon_map, TILE_LOCKED_DOOR)
    assert len(tiles_of(dungeon_map, TILE_STAIRS)) == 1


def test_merchant_does_not_block_stairs_or_key_chest():
    found_merchant = False
    for floor in range(3, 11):
        for seed in range(400):
            random.seed(seed * 31 + floor)
            dungeon_map = Map.generate_random(current_floor=floor)
            merchants = tiles_of(dungeon_map, TILE_MERCHANT)
            if not merchants:
                continue
            found_merchant = True
            reachable = reachable_tiles(
                dungeon_map, blocked=(TILE_WALL, TILE_MERCHANT)
            )
            reachable_no_key = reachable_tiles(
                dungeon_map,
                blocked=(TILE_WALL, TILE_LOCKED_DOOR, TILE_MERCHANT),
            )
            stairs = tiles_of(dungeon_map, TILE_STAIRS)
            assert len(stairs) == 1
            assert stairs[0] in reachable
            if dungeon_map.key_chest_pos is not None:
                assert dungeon_map.key_chest_pos in reachable_no_key
    assert found_merchant
