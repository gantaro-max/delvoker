import random
from constants import (
    TILE_FLOOR, TILE_WALL, TILE_STAIRS, TILE_CHEST,
    TILE_TRAP_SPIKE, TILE_TRAP_POISON, TILE_GRAVE,
    TILE_LOCKED_DOOR, TILE_FOUNTAIN, TILE_MERCHANT,
)


class Map:
    """Dungeon floor tile map with procedural generation and exploration tracking."""

    def __init__(self, tiles, width, height):
        self.tiles   = tiles      # tiles[y][x]
        self.width   = width
        self.height  = height
        self.visited = [[False] * width for _ in range(height)]
        self.start_x = 1
        self.start_y = 1
        self.key_chest_pos = None

    def is_wall(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return True
        return self.tiles[y][x] in (TILE_WALL, TILE_LOCKED_DOOR, TILE_FOUNTAIN, TILE_MERCHANT)

    def tile_at(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return TILE_WALL
        return self.tiles[y][x]

    def visit(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.visited[y][x] = True

    def set_tile(self, x, y, tile):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile

    @staticmethod
    def generate_random(width=20, height=20, grave=None, current_floor=1):
        tiles = [[TILE_WALL] * width for _ in range(height)]
        rooms = []

        for _ in range(25):
            rw = random.randint(3, 6)
            rh = random.randint(3, 5)
            rx = random.randint(1, width - rw - 1)
            ry = random.randint(1, height - rh - 1)
            overlaps = any(
                rx < ox + ow + 1 and rx + rw + 1 > ox and
                ry < oy + oh + 1 and ry + rh + 1 > oy
                for ox, oy, ow, oh in rooms
            )
            if not overlaps:
                for cy in range(ry, ry + rh):
                    for cx in range(rx, rx + rw):
                        tiles[cy][cx] = TILE_FLOOR
                rooms.append((rx, ry, rw, rh))

        for i in range(1, len(rooms)):
            x1 = rooms[i-1][0] + rooms[i-1][2] // 2
            y1 = rooms[i-1][1] + rooms[i-1][3] // 2
            x2 = rooms[i][0]   + rooms[i][2]   // 2
            y2 = rooms[i][1]   + rooms[i][3]   // 2
            cx = x1
            while cx != x2:
                tiles[y1][cx] = TILE_FLOOR
                cx += 1 if x2 > x1 else -1
            cy = y1
            while cy != y2:
                tiles[cy][x2] = TILE_FLOOR
                cy += 1 if y2 > y1 else -1

        if rooms:
            lx, ly, lw, lh = rooms[-1]
            tiles[ly + lh // 2][lx + lw // 2] = TILE_STAIRS

        if len(rooms) >= 2:
            mid = max(1, len(rooms) // 2)
            cr = rooms[mid]
            tiles[cr[1] + cr[3] // 2][cr[0] + cr[2] // 2] = TILE_CHEST

        if rooms:
            start_cx = rooms[0][0] + rooms[0][2] // 2
            start_cy = rooms[0][1] + rooms[0][3] // 2
            if current_floor < 3:
                max_traps = 0
            elif current_floor < 6:
                max_traps = 1
            else:
                max_traps = 2
            for rx, ry, rw, rh in rooms:
                count = random.randint(0, max_traps)
                candidates = [
                    (tcx, tcy)
                    for tcy in range(ry, ry + rh)
                    for tcx in range(rx, rx + rw)
                    if tiles[tcy][tcx] == TILE_FLOOR
                    and not (tcx == start_cx and tcy == start_cy)
                ]
                if candidates and count > 0:
                    chosen = random.sample(candidates, min(count, len(candidates)))
                    for tcx, tcy in chosen:
                        tiles[tcy][tcx] = random.choice([TILE_TRAP_SPIKE, TILE_TRAP_POISON])

        m = Map(tiles, width, height)
        if rooms:
            m.start_x = rooms[0][0] + rooms[0][2] // 2
            m.start_y = rooms[0][1] + rooms[0][3] // 2

        if current_floor < 3:
            return m

        # Place locked doors at corridor chokepoints (30% chance per chokepoint, max 2)
        choke_candidates = []
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if tiles[y][x] != TILE_FLOOR:
                    continue
                h_choke = tiles[y-1][x] == TILE_WALL and tiles[y+1][x] == TILE_WALL
                v_choke = tiles[y][x-1] == TILE_WALL and tiles[y][x+1] == TILE_WALL
                if h_choke or v_choke:
                    if rooms and abs(x - m.start_x) + abs(y - m.start_y) > 4:
                        choke_candidates.append((x, y))
        random.shuffle(choke_candidates)
        doors_placed = 0
        max_doors = 1 if current_floor < 6 else 2
        for cx, cy in choke_candidates:
            if doors_placed >= max_doors:
                break
            if random.random() < 0.3:
                tiles[cy][cx] = TILE_LOCKED_DOOR
                doors_placed += 1

        # Guarantee a dungeon_key chest in an accessible room if any doors were placed
        if doors_placed > 0 and len(rooms) >= 2:
            for r in rooms[1:]:
                kx = r[0] + r[2] // 2
                ky = r[1] + r[3] // 2
                if tiles[ky][kx] not in (TILE_WALL, TILE_LOCKED_DOOR):
                    tiles[ky][kx] = TILE_CHEST
                    m.key_chest_pos = (kx, ky)
                    break

        # Fountain placement (50% chance, any floor, not in start room)
        if rooms and random.random() < 0.5:
            shuffled = list(rooms[1:] if len(rooms) > 1 else rooms)
            random.shuffle(shuffled)
            for rx, ry, rw, rh in shuffled:
                cands = [(fx, fy) for fy in range(ry, ry + rh)
                         for fx in range(rx, rx + rw) if tiles[fy][fx] == TILE_FLOOR]
                if cands:
                    fx, fy = random.choice(cands)
                    tiles[fy][fx] = TILE_FOUNTAIN
                    break

        # Merchant placement (B3F+, 20% chance)
        if current_floor >= 3 and random.random() < 0.2 and len(rooms) >= 3:
            shuffled = list(rooms[2:])
            random.shuffle(shuffled)
            for rx, ry, rw, rh in shuffled:
                cands = [(fx, fy) for fy in range(ry, ry + rh)
                         for fx in range(rx, rx + rw) if tiles[fy][fx] == TILE_FLOOR]
                if cands:
                    fx, fy = random.choice(cands)
                    tiles[fy][fx] = TILE_MERCHANT
                    break

        if grave is not None and grave.floor == current_floor:
            if 0 <= grave.x < width and 0 <= grave.y < height:
                tiles[grave.y][grave.x] = TILE_GRAVE

        return m
