import json
import os
from enum import Enum
from typing import Tuple


class Connection(Enum):
    NONE = "n"
    ANY = "a"
    DIAMOND = "d"
    CROSS = "c"
    MOON = "m"
    GOLD_DIAMOND = "D"
    GOLD_CROSS = "C"
    GOLD_MOON = "M"


def is_golden(c: Connection):
    return (
        c is Connection.GOLD_DIAMOND
        or c is Connection.GOLD_CROSS
        or c is Connection.GOLD_MOON
    )


def valid_connection(a: Connection, b: Connection):
    return (
        a is Connection.NONE
        and b is Connection.NONE
        or (a is not Connection.NONE and b is not Connection.NONE)
    )


def link_connection(a: Connection, b: Connection):
    if not valid_connection(a, b) or not is_matching(a, b):
        return Connection.NONE
    if a is Connection.ANY and b is Connection.ANY:
        return Connection.ANY
    return to_base_connection(a) if a is not Connection.ANY else to_base_connection(b)


def to_base_connection(c: Connection):
    return {
        Connection.GOLD_DIAMOND: Connection.DIAMOND,
        Connection.GOLD_CROSS: Connection.CROSS,
        Connection.GOLD_MOON: Connection.MOON,
    }.get(c, c)


def is_matching(a: Connection, b: Connection):
    if not valid_connection(a, b):
        return False
    if a is Connection.ANY or b is Connection.ANY:
        return True
    return to_base_connection(a) is to_base_connection(b)


class Room:
    @staticmethod
    def make_throne_room():
        return Room.make(1, "Throne Room", "aaaa")

    @staticmethod
    def make(unique_id: int, name: str, connections: str):
        return Room(
            unique_id,
            name,
            (
                Connection(connections[0]),
                Connection(connections[1]),
                Connection(connections[2]),
                Connection(connections[3]),
            ),
        )

    def __init__(
        self,
        unique_id: int,
        name: str,
        connections: Tuple[Connection, Connection, Connection, Connection],
    ):
        up, right, down, left = connections
        self.unique_id = unique_id
        self.name = name
        self.up = up
        self.right = right
        self.down = down
        self.left = left
        self.pos: Tuple[int, int] = None  # type: ignore

    def rotate_right(self):
        return Room(
            self.unique_id, self.name, (self.left, self.up, self.right, self.down)
        )

    def rotate_left(self):
        return Room(
            self.unique_id, self.name, (self.right, self.down, self.left, self.up)
        )


def all_rooms():
    with open(os.path.join("disastle", "data", "room_list.json")) as file:
        room_dict = json.load(file)
        for unique_id in room_dict:
            yield Room.make(unique_id, room_dict[unique_id][0], room_dict[unique_id][1])
