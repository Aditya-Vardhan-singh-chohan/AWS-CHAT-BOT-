import random
from typing import List

from model import Castle, Game, Player
from data.room_list import ROOM_LIST
from data.disaster_list import DISASTER_LIST


SHOP_SIZE = 5
THRONE_ROOM_ID_START = 101


def is_game_ended(game_info: Game) -> bool:
    return (
        len(game_info.previous_disasters)
        == game_info.num_catastrophes + game_info.num_disasters
    )


def action_discard(
    game_info: Game, player_id: str, discard_list: List[str]
) -> Game:
    if (
        len(game_info.current_disasters) == 0
        or player_damage(game_info, player_id) == 0
        or len(discard_list) != player_damage(game_info, player_id)
    ):
        return game_info
    copied_castle = game_info.players[player_id].castle.copy()
    try:
        copied_castle.discard(*discard_list)
    except RuntimeError:
        return game_info
    game_info.players[player_id].discard_list = discard_list
    game_info = resolve_disaster(game_info)
    return game_info


def action_shop(
    game_info: Game,
    player_id: str,
    room_id: int,
    x: int,
    y: int,
    rotation: int = 0,
) -> Game:
    if room_id not in game_info.shop:
        return game_info
    castle = game_info.players[player_id].castle
    try:
        castle.place(room_id, x, y, rotation)
    except RuntimeError:
        return game_info
    game_info.shop.remove(room_id)
    game_info = pass_turn(game_info)
    return game_info


def action_move(
    game_info: Game,
    player_id: str,
    room_id: int,
    x: int,
    y: int,
    rotation: int = 0,
) -> Game:
    try:
        game_info.players[player_id].castle.move(room_id, x, y, rotation)
    except RuntimeError:
        return game_info
    game_info = pass_turn(game_info)
    return game_info


def action_swap(
    game_info: Game,
    player_id: str,
    room_id_a: int,
    room_id_b: int,
    rotation_a: int,
    rotation_b: int,
) -> Game:
    try:
        game_info.players[player_id].castle.swap(
            room_id_a, room_id_b, rotation_a, rotation_b
        )
    except RuntimeError:
        return game_info
    game_info = pass_turn(game_info)
    return game_info


def translate_disaster_connection_damage(
    encoding: str, num_previous_disasters: int
) -> int:
    damage = 0
    for term in encoding.split("+"):
        if "x" in term:
            damage += int(term.strip("x")) * num_previous_disasters
        else:
            damage += int(term)
    return damage


def disaster_damage(game_info: Game, disaster_id: str, player_id: str) -> int:
    num_previous_disasters = len(game_info.previous_disasters)
    diamond_damage = translate_disaster_connection_damage(
        DISASTER_LIST[disaster_id]["diamond"], num_previous_disasters
    )
    cross_damage = translate_disaster_connection_damage(
        DISASTER_LIST[disaster_id]["cross"], num_previous_disasters
    )
    moon_damage = translate_disaster_connection_damage(
        DISASTER_LIST[disaster_id]["moon"], num_previous_disasters
    )
    diamond, cross, moon, wild = game_info.players[player_id].castle
    diamond_damage = max(diamond_damage - diamond, 0)
    cross_damage = max(cross_damage - cross, 0)
    moon_damage = max(moon_damage - moon, 0)
    return max(diamond_damage + cross_damage + moon_damage - wild, 0)


def player_damage(game_info: Game, player_id: str) -> int:
    if len(game_info.current_disasters) == 0:
        return 0
    return disaster_damage(
        game_info, game_info.current_disasters[0], player_id
    )


def all_discard_complete(game_info: Game):
    for player_id in game_info.players:
        num_discarded = len(game_info.players[player_id].discard_list)
        if player_damage(game_info, player_id) - num_discarded > 0:
            return False
    return True


def resolve_disaster(game_info: Game) -> Game:
    if all_discard_complete(game_info):
        game_info.previous_disasters.append(game_info.current_disasters.pop())
        for player_id in game_info.players:
            castle = game_info.players[player_id].castle
            castle.discard(*game_info.players[player_id].discard_list)
            game_info.players[player_id].discard_list = []
    return game_info


def pass_turn(game_info: Game) -> Game:
    game_info.turn_index = game_info.turn_index + 1
    if game_info.turn_index >= len(game_info.turn_order):
        game_info.turn_index = 0
        game_info.turn_order = (
            game_info.turn_order[1:] + game_info.turn_order[0]
        )
        game_info = restock_shop(game_info)
    return game_info


def restock_shop(game_info: Game) -> Game:
    """
    Discard current shop, restock shop and put aside any disasters
    that are supposed to be resolved this turn
    """
    if len(game_info.current_disasters) > 0:
        raise RuntimeError("Must resolve disaster first before restocking")
    # Discard remaining shop
    game_info.discard.extend(game_info.shop)
    game_info.shop = []
    # Deal shop
    while len(game_info.shop) < SHOP_SIZE and len(game_info.deck) > 0:
        if len(game_info.deck) > 0:
            card = game_info.deck.pop()
        else:
            # Randomly take from discard pile if deck is empty
            discard_index = random.choice(range(len(game_info.discard)))
            card = game_info.discard.pop(discard_index)
        if card[0] == "d" or card[0] == "c":
            game_info.current_disasters.append(card)
        else:
            game_info.shop.append(int(card))
    if len(game_info.current_disasters) > 1 and len(game_info.deck) >= len(
        game_info.current_disasters
    ):
        # Shuffle back all but the first dealt disaster
        game_info.deck.extend(game_info.shop + game_info.current_disasters[1:])
        game_info.current_disasters = game_info.current_disasters[0:1]
        game_info.shop = []
        random.shuffle(game_info.deck)
        # Redeal shop
        while len(game_info.shop) < SHOP_SIZE:
            if len(game_info.deck) > 0:
                card = game_info.deck.pop()
            else:
                # Randomly take from discard pile if deck is empty
                discard_index = random.choice(range(len(game_info.discard)))
                card = game_info.discard.pop(discard_index)
            if card[0] == "d" or card[0] == "c":
                game_info.current_disasters.append(card)
            else:
                game_info.shop.append(int(card))
        game_info.discard = game_info.deck
    if len(game_info.current_disasters) > 0 and all_discard_complete(
        game_info
    ):
        game_info = resolve_disaster(game_info)
    return game_info


def shuffle_turn_order(game_info: Game) -> Game:
    random.shuffle(game_info.turn_order)
    return game_info


def create_game(
    players_info: dict,
    num_disasters: int,
    num_catastrophes: int,
    num_safe: int,
) -> Game:
    if num_safe < SHOP_SIZE:
        raise RuntimeError("At least the first shop must be safe")

    deck = []
    for room_id in ROOM_LIST:
        room = int(room_id)
        if room < THRONE_ROOM_ID_START:
            deck.append(room)
    random.shuffle(deck)
    safe = deck[:num_safe]
    deck = deck[num_safe:]
    disasters = []
    catastrophes = []
    for card in DISASTER_LIST:
        if card[0] == "d":
            disasters += [card]
        elif card[0] == "c":
            catastrophes += [card]
    deck += random.sample(disasters, num_disasters) + random.sample(
        catastrophes, num_catastrophes
    )
    random.shuffle(deck)
    deck = deck + safe
    shop = []
    while len(shop) < SHOP_SIZE:
        shop.append(deck.pop())
    players = {}
    for player_id in players_info:
        info = players_info[player_id]
        players[player_id] = Player(
            info["username"],
            int(info["throne_room_id"]),
            Castle(int(info["throne_room_id"])).to_json_obj(),
            [],
        )
    turn_order = [player_id for player_id in players_info]
    random.shuffle(turn_order)
    return Game(
        players,
        turn_order,
        0,
        shop,
        [],
        deck,
        num_disasters,
        num_catastrophes,
        [],
        [],
    )
