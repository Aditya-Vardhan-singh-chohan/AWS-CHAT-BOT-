import random
from itertools import product
from typing import Dict, List, Tuple

from disastle import disasters
from disastle import rooms
from disastle.castle import Castle


def shuffled(l: list):
    temp = list(l)
    return random.sample(temp, len(temp))


class Game:
    @staticmethod
    def get_disasters(disaster_num: int, catastrophe_num: int):
        return random.sample(
            list(disasters.all_disasters()), disaster_num
        ) + random.sample(list(disasters.all_catastrophes()), catastrophe_num)

    def __init__(
        self,
        player_list: List[str],
        disaster_num: int,
        catastrophe_num: int,
        safe_num: int = 15,
    ):
        self.init_deck(disaster_num, catastrophe_num, safe_num)
        self.players = shuffled(list(player_list))
        self.castle: Dict[str, Castle] = {}
        for player in player_list:
            self.castle[player] = Castle()
        self.round = 0
        self.first_index = 0
        self.turn_done = False
        self.shop = list(self.deal(5))

    def buy(self, unique_id: int, x: int, y: int):
        """Play a card with the index from the shop"""
        room = next(r for r in self.shop if r.unique_id == unique_id)
        self.turn_castle().place(room, x, y)
        del self.shop[self.shop.index(room)]
        self.turn_done = True

    def move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        player_castle = self.turn_castle()
        room = player_castle.get(*from_pos)
        player_castle.remove(*from_pos)
        player_castle.place(room, *to_pos)
        self.turn_done = True

    def swap(self, pos_1: Tuple[int, int], pos_2: Tuple[int, int]):
        player_castle = self.turn_castle()
        room_1 = player_castle.get(*pos_1)
        player_castle.set(player_castle.get(*pos_2), *pos_1)
        player_castle.set(room_1, *pos_2)

    def possible_buy_actions(self):
        player_castle = self.turn_castle()
        for room, pos in product(self.shop, player_castle.free_pos()):
            if player_castle.place_valid(room, *pos):
                yield (self.buy, [room.unique_id, pos[0], pos[1]])

    def possible_move_actions(self):
        player_castle = self.turn_castle()
        for room, new_pos in product(
            player_castle.outer_rooms(), player_castle.free_pos()
        ):
            old_pos = room.pos
            if player_castle.move_valid(room, old_pos, new_pos):
                yield (self.move, [old_pos, new_pos])

    def possible_swap_actions(self):
        player_castle = self.turn_castle()
        for room_1, room_2 in product(player_castle.rooms, repeat=2):
            if player_castle.swap_valid(room_1.pos, room_2.pos):
                yield (self.swap, [room_1.pos, room_2.pos])

    def possible_actions(self):
        if self.turn_done:
            return [(self.pass_turn, [])]
        return (
            list(self.possible_buy_actions())
            + list(self.possible_move_actions())
            + list(self.possible_swap_actions())
            + [(self.pass_turn, [])]
        )

    def turn_player(self):
        return self.players[self.first_index]

    def turn_castle(self):
        return self.castle[self.turn_player()]

    def pass_turn(self):
        self.first_index += 1
        if self.first_index % len(self.players) == 0:
            self.first_index = 0
            self.players = self.players[1:] + self.players[:1]
            self.round += 1
        self.turn_done = False

    def init_deck(self, disaster_num: int, catastrophe_num: int, safe_num: int):
        self.deck = shuffled(list(rooms.all_rooms()))
        safe_cards = self.deck[-safe_num:]
        self.deck = self.deck[:-safe_num]
        self.deck = (
            shuffled(self.deck + Game.get_disasters(disaster_num, catastrophe_num))
            + safe_cards
        )

    def deal(self, num: int = 1):
        redealt = False
        disaster_count = 0
        for _ in range(num):
            card = self.deck.pop()
            if isinstance(card, disasters.Disaster):
                disaster_count += 1
                if disaster_count > 1 and not redealt:
                    redealt = True
                    self.deck.append(card)
                    self.deck = shuffled(self.deck)
                    card = self.deck.pop()
            yield card
