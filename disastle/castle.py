from rooms import Connection, Room, valid_connection, link_connection, isGolden
from typing import Tuple


class Castle:
    def __init__(self):
        self.rooms = set()
        self.grid = []
        for _ in range(101):
            col = []
            for _ in range(101):
                col.append(None)
            self.grid.append(col)
        self.place(Room.make_throne_room(), 0, 0)

    def get(self, x: int, y: int) -> Room:
        gx, gy = Castle.grid_pos(x, y)
        return self.grid[gx][gy]

    def set(self, room: Room, x: int, y: int):
        gx, gy = Castle.grid_pos(x, y)
        self.grid[gx][gy] = room

    def place(self, room: Room, x: int, y: int):
        if not self.place_valid(room, x, y):
            raise ValueError(x, y, "is not a valid room placement")
        room.pos = (x, y)
        self.set(room, x, y)
        self.rooms.add(room)

    def remove(self, x: int, y: int):
        room = self.get(x, y)
        if room is None:
            raise ValueError("No room in", x, y, "position")
        room.pos = None  # type: ignore
        self.rooms.remove(room)
        self.set(None, x, y)  # type: ignore

    def swap_valid(self, pos_1: Tuple[int, int], pos_2: Tuple[int, int]):
        return (
            pos_1 != pos_2
            and self.place_valid(self.get(*pos_1), *pos_2)
            and self.place_valid(self.get(*pos_2), *pos_1)
        )

    def move_valid(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        room = self.get(*from_pos)
        self.remove(*from_pos)
        result = self.place_valid(room, *to_pos)
        self.place(room, *from_pos)
        return result

    def place_valid(self, room: Room, x: int, y: int):
        if len(self.rooms) == 0 and x == y == 0:
            return True
        if (
            Castle.out_of_bounds(x, y + 1)
            or Castle.out_of_bounds(x + 1, y)
            or Castle.out_of_bounds(x, y - 1)
            or Castle.out_of_bounds(x - 1, y)
        ):
            return False
        up_room = self.get(x, y + 1)
        right_room = self.get(x + 1, y)
        down_room = self.get(x, y - 1)
        left_room = self.get(x - 1, y)
        return (
            (up_room is None or valid_connection(up_room.down, room.up))
            and (right_room is None or valid_connection(right_room.left, room.right))
            and (down_room is None or valid_connection(down_room.up, room.down))
            and (left_room is None or valid_connection(left_room.right, room.left))
        )

    def surrounding(self, x: int, y: int):
        result = {}
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                # Skip center
                if dx == 0 and dy == 0:
                    continue
                px, py = x + dx, y + dy
                # Skip if new coords out of bounds.
                if Castle.out_of_bounds(px, py):
                    continue
                result[(px, py)] = self.get(px, py)
        return result

    def outer_rooms(self):
        for room in self.rooms:
            if self.is_outer_room(*room.pos):
                yield room

    def is_outer_room(self, x: int, y: int):
        return list(self.connected(x, y).values()).count(None) == 1

    def connected(self, x: int, y: int):
        d_list = []
        room = self.get(x, y)
        if room is None:
            raise ValueError("No room found at", x, y)
        if room.up is not Connection.NONE:
            d_list.append((0, 1))
        if room.right is not Connection.NONE:
            d_list.append((1, 0))
        if room.down is not Connection.NONE:
            d_list.append((0, -1))
        if room.left is not Connection.NONE:
            d_list.append((-1, 0))
        result = {}
        for dx, dy in d_list:
            px, py = x + dx, y + dy
            # Skip if new coords out of bounds.
            if Castle.out_of_bounds(px, py):
                continue
            result[(px, py)] = self.get(px, py)
        return result

    def free_pos(self):
        result = set()
        for room in self.rooms:
            x, y = room.pos
            connected_rooms = self.connected(x, y)
            for pos in connected_rooms:
                if connected_rooms[pos] is None:
                    result.add(pos)
        return result

    def is_powered(self, x: int, y: int):
        powered = True
        connected_rooms = self.connected(x, y)
        for c_x, c_y in connected_rooms:
            dx, dy = (x - c_x, y - c_y)
            if (dx, dy) == (0, -1):
                if isGolden(room.up):
                    powered = powered and is_matching(
                        room.up, connected_rooms[(c_x, c_y)].down
                    )
            elif (dx, dy) == (-1, 0):
                if isGolden(room.right):
                    powered = powered and is_matching(
                        room.right, connected_rooms[(c_x, c_y)].left
                    )
            elif (dx, dy) == (0, 1):
                if isGolden(room.down):
                    powered = powered and is_matching(
                        room.down, connected_rooms[(c_x, c_y)].up
                    )
            elif (dx, dy) == (1, 0):
                if isGolden(room.left):
                    powered = powered and is_matching(
                        room.left, connected_rooms[(c_x, c_y)].right
                    )
            else:
                raise ValueError("castle.connected did not return a connected room")
        return powered

    def links(self):
        diamond, cross, moon, reduction = (0, 0, 0, 0)
        for room in self.rooms:
            connected_rooms = self.connected(*room.pos)
            for c_x, c_y in connected_rooms:
                x, y = room.pos
                dx, dy = (x - c_x, y - c_y)
                if (dx, dy) == (0, -1):
                    connection = link_connection(
                        room.up, connected_rooms[(c_x, c_y)].down
                    )
                    if connection is Connection.DIAMOND:
                        diamond += 1
                    elif connection is Connection.CROSS:
                        cross += 1
                    elif connection is Connection.MOON:
                        moon += 1
                    elif connection is Connection.ANY:
                        reduction += 1
                elif (dx, dy) == (1, 0):
                    connection = link_connection(
                        room.right, connected_rooms[(c_x, c_y)].left
                    )
                    if connection is Connection.DIAMOND:
                        diamond += 1
                    elif connection is Connection.CROSS:
                        cross += 1
                    elif connection is Connection.MOON:
                        moon += 1
                    elif connection is Connection.ANY:
                        reduction += 1
                elif (dx, dy) == (0, 1):
                    connection = link_connection(
                        room.down, connected_rooms[(c_x, c_y)].up
                    )
                    if connection is Connection.DIAMOND:
                        diamond += 1
                    elif connection is Connection.CROSS:
                        cross += 1
                    elif connection is Connection.MOON:
                        moon += 1
                    elif connection is Connection.ANY:
                        reduction += 1
                elif (dx, dy) == (-1, 0):
                    connection = link_connection(
                        room.left, connected_rooms[(c_x, c_y)].right
                    )
                    if connection is Connection.DIAMOND:
                        diamond += 1
                    elif connection is Connection.CROSS:
                        cross += 1
                    elif connection is Connection.MOON:
                        moon += 1
                    elif connection is Connection.ANY:
                        reduction += 1
                else:
                    raise ValueError("self.connected did not return a connected room")
        return (diamond / 2, cross / 2, moon / 2, reduction / 2)

    @staticmethod
    def out_of_bounds(x: int, y: int):
        return x < -50 or x > 50 or y < -50 or y > 50

    @staticmethod
    def grid_pos(x: int, y: int):
        if Castle.out_of_bounds(x, y):
            return ValueError("x or y must be in [-50, 50]")
        return (x + 50, y + 50)
