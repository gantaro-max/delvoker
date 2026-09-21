from collections import deque
import random

from constants import (
    TILE_CHEST,
    TILE_LOCKED_DOOR,
    TILE_MERCHANT,
    TILE_STAIRS,
    TILE_WALL,
)
from logic.map_generator import Map


def reachable_tiles(dungeon_map):
    start = (dungeon_map.start_x, dungeon_map.start_y)
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < dungeon_map.width and 0 <= ny < dungeon_map.height):
                continue
            if dungeon_map.tiles[ny][nx] == TILE_WALL or (nx, ny) in seen:
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
    for seed in range(100):
        random.seed(seed)
        dungeon_map = Map.generate_random(current_floor=3)
        if not tiles_of(dungeon_map, TILE_LOCKED_DOOR):
            continue
        found_door = True
        assert dungeon_map.key_chest_pos is not None
        x, y = dungeon_map.key_chest_pos
        assert dungeon_map.tiles[y][x] == TILE_CHEST
        assert (x, y) in reachable_tiles(dungeon_map)
    assert found_door
