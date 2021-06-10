import numpy as np

from typing import List, Tuple, Dict

from data.room_list import ROOM_LIST

ALL_CONNECTIONS = " *dDxXmM"


class Castle:
    @staticmethod
    def from_json_obj(throne_room_id: int, from_json_obj: List[str]):
        castle = Castle(throne_room_id)
        castle._data = np.array([[int(r) for r in li] for li in from_json_obj])
        return castle

    def to_json_obj(self) -> List:
        return self._data.tolist()

    def __init__(self, throne_room_id: int):
        self.room_list = {}
        for index in ROOM_LIST:
            if not set(ROOM_LIST[index]["connections"]).issubset(
                ALL_CONNECTIONS
            ):
                raise RuntimeError("Invalid connections in room list")
            self.room_list[int(index)] = ROOM_LIST[index]

        if throne_room_id not in self.room_list:
            raise KeyError("Throne room id not found in room list")
        self.throne_room_id = throne_room_id

        self._data = np.zeros((len(self.room_list) + 1, 4), dtype=np.int)
        self._data[throne_room_id] = [1, 0, 0, 0]

    def all_rooms(self) -> np.array:
        return (self._data[:, 0] > 0).nonzero()[0]

    def get_rotated_connections(self, room_id: int, rotation: int):
        if rotation not in [0, 90, 180, 270]:
            raise RuntimeError(
                "Invalid room rotation. Rotation is {}. ".format(rotation)
                + "Can only be 0, 90, 180 and 270."
            )
        room_connections = self.room_list[room_id]["connections"]
        rotate_num = rotation // 90
        rotated_connections = (
            room_connections[-rotate_num:] + room_connections[:-rotate_num]
        )
        return rotated_connections

    def place(self, room_id: int, x: int, y: int, rotation: int = 0):
        """
        (and rotate if applicable)
        Checks for already placed rooms and improperly matched connections
        """
        if self._data[room_id, 0] > 0:
            raise RuntimeError("Room already placed")
        room_connections = self.get_rotated_connections(room_id, rotation)
        adj_coords = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1), y]

        connected = False
        valid_placement = True
        has_adj = False
        for adj_id in self.all_rooms():
            adj_coord = tuple(self._data[adj_id, 1:3])
            adj_rot = self._data[adj_id, -1]
            try:
                i = adj_coords.index(adj_coord)
                has_adj = True

                conn = room_connections[i]
                adj_room_connections = self.get_rotated_connections(
                    adj_id, adj_rot
                )
                adj_conn = adj_room_connections[(i + 2) % 4]
                if conn != " " and adj_conn != " ":
                    connected = True
                    continue
                elif conn != " " or adj_conn != " ":
                    valid_placement = False
                    break
            except ValueError:
                # adj_id is not adjacent to room_id, skip
                continue

        if not valid_placement or not connected or not has_adj:
            raise RuntimeError("Invalid room placement")
        self._data[room_id] = [1, x, y, rotation]

    def remove(self, room_id: int):
        """
        Unsafe removal of room from the castle
        """
        if self._data[room_id, 0] == 0:
            raise RuntimeError(
                "Room cannot be removed because it's not placed"
            )
        self._data[room_id] = [0, 0, 0, 0]

    def discard(self, *room_ids: int):
        """
        Save and checked removal of room from the castle.
        If multiple room_ids are inputted, it will be discarded sequentially
        """
        backup_data = self._data.copy()
        try:
            for room_id in room_ids:
                if not self.is_outer_room(room_id):
                    raise RuntimeError("Room cannot be discarded")
                self.remove(room_id)
        except RuntimeError:
            self._data = backup_data
            raise RuntimeError("Discard room failed")

    def copy(self):
        copied = Castle(self.throne_room_id)
        copied._data = self._data.copy()
        return copied

    def swap(self, id_a: int, id_b: int, rot_a: int = 0, rot_b: int = 0):
        """
        Checks for anything remove and place checks.
        Essenstially remove both rooms and place them back in swapped.
        """
        backup_data = self._data.copy()
        try:
            self.remove(id_a)
            self.remove(id_b)
        except RuntimeError:
            self._data = backup_data
            raise RuntimeError(
                "Rooms cannot be swapped because they are not placed"
            )
        try:
            self.place(id_b, *backup_data[id_a][1:], rot_a)
            self.place(id_a, *backup_data[id_b][1:], rot_b)
        except RuntimeError:
            self._data = backup_data
            raise RuntimeError(
                "Rooms cannot be swapped because their connections don't match"
            )

    def is_outer_room(self, room_id: int):
        if self._data[room_id, 0] == 0:
            raise RuntimeError("Room is not placed")
        x, y = self._data[room_id, 1:3]
        curr_rot = self._data[room_id, -1]
        room_connections = self.get_rotated_connections(room_id, curr_rot)
        adj_coords = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1), y]

        connected_count = 0
        for adj_id in self.all_rooms():
            adj_coord = tuple(self._data[adj_id, 1:3])
            adj_rot = self._data[adj_id, -1]
            try:
                i = adj_coords.index(adj_coord)
                conn = room_connections[i]
                adj_room_connections = self.get_rotated_connections(
                    adj_id, adj_rot
                )
                adj_conn = adj_room_connections[(i + 2) % 4]
                if conn != " " and adj_conn != " ":
                    connected_count += 1
                    continue
            except ValueError:
                # adj_id is not adjacent to room_id, skip
                continue
        return connected_count == 1

    def rotate(self, room_id: int, rotation: int):
        if self._data[room_id, 0] == 0:
            raise RuntimeError(
                "Room cannot be rotated because it's not placed"
            )
        backup_data = self._data.copy()
        self.remove(room_id)
        try:
            x, y = self._data[room_id, 1:3]
            self.place(room_id, x, y, rotation)
        except RuntimeError:
            self._data = backup_data
            raise RuntimeError(
                "Rooms cannot be rotated because connections don't match"
            )

    def move(self, room_id: int, x: int, y: int, rotation: int = 0):
        """
        (and rotate if applicable)
        """
        if self._data[room_id, 0] == 0:
            raise RuntimeError("Room cannot be moved because it's not placed")
        if not self.is_outer_room(room_id):
            raise RuntimeError(
                "Room cannot be moved because it isn't an outer room"
            )
        backup_data = self._data.copy()
        self.remove(room_id)
        try:
            self.place(room_id, x, y, rotation)
        except RuntimeError:
            self._data = backup_data
            raise RuntimeError(
                "Rooms cannot be moved because connections don't match"
            )

    def num_connections(self) -> Tuple[int, int, int, int]:
        diamond = 0
        cross = 0
        moon = 0
        wild = 0
        for room_id in self.all_rooms():
            x, y = self._data[room_id, 1:3]
            curr_rot = self._data[room_id, -1]
            room_connections = self.get_rotated_connections(room_id, curr_rot)
            adj_coords = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1), y]

            for adj_id in self.all_rooms():
                adj_coord = tuple(self._data[adj_id, 1:3])
                adj_rot = self._data[adj_id, -1]
                try:
                    i = adj_coords.index(adj_coord)
                    conn = room_connections[i]
                    adj_room_connections = self.get_rotated_connections(
                        adj_id, adj_rot
                    )
                    adj_conn = adj_room_connections[(i + 2) % 4]
                    if conn == "*" and adj_conn == "*":
                        wild += 1
                    elif conn in "dD*" and adj_conn in "dD*":  # noqa: F632
                        diamond += 1
                    elif conn in "xX*" and adj_conn in "xX*":  # noqa: F632
                        cross += 1
                    elif conn in "mM*" and adj_conn in "mM*":  # noqa: F632
                        moon += 1
                except ValueError:
                    # adj_id is not adjacent to room_id, skip
                    continue
        return diamond // 2, cross // 2, moon // 2, wild // 2


class Player:
    def from_json_obj(self, json_obj):
        discard_list = [int(c) for c in json_obj["discard_list"]]
        return Player(
            json_obj["username"],
            int(json_obj["throne_room_id"]),
            json_obj["castle_list"],
            discard_list,
        )

    def to_json_obj(self) -> dict:
        return {
            "username": self.username,
            "throne_room_id": self.castle.throne_room_id,
            "castle_list": self.castle.to_json_obj(),
            "discard_list": self.discard_list,
        }

    def __init__(self, username, throne_room_id, castle_list, discard_list):
        self.username = username
        self.castle = Castle.from_json_obj(throne_room_id, castle_list)
        self.discard_list = discard_list


class Game:
    @staticmethod
    def from_json_obj(json_obj: dict):
        players = {}
        for player_id in json_obj["players"]:
            players[player_id] = Player(json_obj["players"][player_id])
        turn_order = [int(t) for t in json_obj["turn_order"]]
        shop = [int(t) for t in json_obj["shop"]]
        discard = [int(t) for t in json_obj["discard"]]
        game = Game(
            players,
            turn_order,
            int(json_obj["turn_index"]),
            shop,
            discard,
            json_obj["deck"],
            int(json_obj["num_disasters"]),
            int(json_obj["num_catastrophes"]),
            json_obj["current_disasters"],
            json_obj["previous_disasters"],
        )
        return game

    def to_json_obj(self) -> dict:
        players: dict[str, dict] = {}
        for player_id in self.players:
            players[player_id] = self.players[player_id].to_json_obj()
        return {
            "players": players,
            "turn_order": self.turn_order,
            "turn_index": self.turn_index,
            "shop": self.shop,
            "discard": self.discard,
            "deck": self.deck,
            "num_disasters": self.num_disasters,
            "num_catastrophes": self.num_disasters,
            "current_disasters": self.current_disasters,
            "previous_disasters": self.previous_disasters,
        }

    def to_public_json_obj(self) -> dict:
        players = []
        for player_id in self.players:
            players.append(self.players[player_id].to_json_obj())
        turn_order = []
        for id in self.turn_order:
            turn_order.append(self.players[id].username)
        return {
            "players": players,
            "name_turn_order": turn_order,
            "shop": self.shop,
            "discard": self.discard,
            "num_disasters": self.num_disasters,
            "num_catastrophes": self.num_disasters,
            "current_disasters": self.current_disasters,
            "previous_disasters": self.previous_disasters,
        }

    def __init__(
        self,
        players: Dict[str, Player],
        turn_order: List[str],
        turn_index: int,
        shop: List[int],
        discard: List[int],
        deck: List[str],
        num_disasters: int,
        num_catastrophes: int,
        current_disasters: List[str],
        previous_disasters: List[str],
    ):
        self.players: Dict[str, Player] = players
        self.turn_order = turn_order
        self.turn_index = turn_index
        self.shop = shop
        self.discard = discard
        self.deck = deck
        self.num_disasters = num_disasters
        self.num_catastrophes = num_catastrophes
        self.current_disasters = current_disasters
        self.previous_disasters = previous_disasters
