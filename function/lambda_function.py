import os
import logging
import uuid

from datetime import datetime
from typing import Dict

import jsonpickle
import boto3
from boto3.dynamodb.conditions import Key

# from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

import manager
from model import Game

logger = logging.getLogger()
logger.setLevel(logging.INFO)
patch_all()

client = boto3.client("lambda")
client.get_account_settings()

# Get the service resource.
dynamodb = boto3.resource("dynamodb")

# Instantiate a table resource object without actually
# creating a DynamoDB table. Note that the attributes of this table
# are lazy-loaded: a request is not made nor are the attribute
# values populated until the attributes
# on the table resource are accessed or its load() method is called.
game_table = dynamodb.Table("disastle_game")

NUM_DISASTER_DEFAULT = 6
NUM_CATASTROPHES_DEFAULT = 0
NUM_SAFE_DEFAULT = 15


def lambda_handler(event, context):
    logger.info(
        "## ENVIRONMENT VARIABLES\r" + jsonpickle.encode(dict(**os.environ))
    )
    logger.info("## EVENT\r" + jsonpickle.encode(event))
    logger.info("## CONTEXT\r" + jsonpickle.encode(context))

    if event["action"] == "CREATE_LOBBY":
        return create_lobby(event)
    elif event["action"] == "JOIN_LOBBY":
        return join_lobby(event)
    elif event["action"] == "MODIFY_LOBBY":
        return modify_lobby(event)
    elif event["action"] == "READY_LOBBY":
        return ready_lobby(event)
    elif event["action"] == "START_GAME":
        return start_game(event)
    elif event["action"] == "GET_GAME_INFO":
        return get_game_info(event)
    elif event["action"] == "ACTION_DISCARD":
        return discard(event)
    elif event["action"] == "ACTION_SHOP":
        return shop(event)
    elif event["action"] == "ACTION_MOVE":
        return move(event)
    elif event["action"] == "ACTION_SWAP":
        return swap(event)
    return {}


def discard(event) -> Dict:
    if (
        "game_id" not in event
        or "game_timestamp" not in event
        or "player_id" not in event
        or "discard_list" not in event
    ):
        return {}
    response = game_table.get_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]}
    )
    if response["Item"]["game_state"] != "PLAYING":
        return {}
    game_info = Game.from_json_obj(response["Item"])
    game_info = manager.action_discard(
        game_info, event["player_id"], event["discard_list"]
    )
    if manager.is_game_ended(game_info):
        update_game(
            event["game_id"], event["game_timestamp"], game_info, "ENDED"
        )
    else:
        update_game(
            event["game_id"], event["game_timestamp"], game_info, "PLAYING"
        )
    return {
        "player_id": event["player_id"],
        "game_id": event["game_id"],
        "game_timestamp": event["game_timestamp"],
    }


def shop(event) -> Dict:
    if (
        "game_id" not in event
        or "game_timestamp" not in event
        or "player_id" not in event
        or "room_id" not in event
        or "x" not in event
        or "y" not in event
        or "rotation" not in event
    ):
        return {}
    response = game_table.get_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]}
    )
    if response["Item"]["game_state"] != "PLAYING":
        return {}
    game_info = Game.from_json_obj(response["Item"])
    game_info = manager.action_shop(
        game_info,
        event["player_id"],
        event["room_id"],
        event["x"],
        event["y"],
        event["rotation"],
    )
    update_game(
        event["game_id"], event["game_timestamp"], game_info, "PLAYING"
    )
    return {
        "player_id": event["player_id"],
        "game_id": event["game_id"],
        "game_timestamp": event["game_timestamp"],
    }


def move(event) -> Dict:
    if (
        "game_id" not in event
        or "game_timestamp" not in event
        or "player_id" not in event
        or "room_id" not in event
        or "x" not in event
        or "y" not in event
        or "rotation" not in event
    ):
        return {}
    response = game_table.get_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]}
    )
    if response["Item"]["game_state"] != "PLAYING":
        return {}
    game_info = Game.from_json_obj(response["Item"])
    game_info = manager.action_move(
        game_info,
        event["player_id"],
        event["room_id"],
        event["x"],
        event["y"],
        event["rotation"],
    )
    update_game(
        event["game_id"], event["game_timestamp"], game_info, "PLAYING"
    )
    return {
        "player_id": event["player_id"],
        "game_id": event["game_id"],
        "game_timestamp": event["game_timestamp"],
    }


def swap(event) -> Dict:
    if (
        "game_id" not in event
        or "game_timestamp" not in event
        or "player_id" not in event
        or "room_id_a" not in event
        or "room_id_b" not in event
        or "rotation_a" not in event
        or "rotation_b" not in event
    ):
        return {}
    response = game_table.get_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]}
    )
    if response["Item"]["game_state"] != "PLAYING":
        return {}
    game_info = Game.from_json_obj(response["Item"])
    game_info = manager.action_move(
        game_info,
        event["player_id"],
        event["room_id_a"],
        event["room_id_b"],
        event["rotation_a"],
        event["rotation_b"],
    )
    update_game(
        event["game_id"], event["game_timestamp"], game_info, "PLAYING"
    )
    return {
        "player_id": event["player_id"],
        "game_id": event["game_id"],
        "game_timestamp": event["game_timestamp"],
    }


def get_game_info(event) -> Dict:
    if "game_id" not in event or "game_timestamp" not in event:
        return {}
    response = game_table.get_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]}
    )
    game_info = Game.from_json_obj(response["Item"])
    return {
        "game_id": event["game_id"],
        "game_timestamp": event["game_timestamp"],
        "game_info": game_info.to_public_json_obj(),
    }


def start_game(event) -> Dict[str, str]:
    if (
        "game_id" not in event
        or "game_timestamp" not in event
        or "player_id" not in event
    ):
        return {}
    response = game_table.get_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]}
    )
    game_info = response["Item"]
    players_info = game_info["players"]

    # Check ready: already chosen throne_room_id
    if event["player_id"] not in players_info or any(
        "throne_room_id" not in players_info[player] for player in players_info
    ):
        return {}
    game = manager.create_game(
        players_info,
        int(game_info["num_disasters"]),
        int(game_info["num_catastrophes"]),
        int(game_info["num_safe"]),
    )
    update_game(event["game_id"], event["game_timestamp"], game, "PLAYING")
    return {
        "player_id": event["player_id"],
        "game_id": event["game_id"],
        "game_timestamp": event["game_timestamp"],
    }


def ready_lobby(event) -> Dict[str, str]:
    if (
        "game_id" not in event
        or "game_timestamp" not in event
        or "player_id" not in event
        or "throne_room_id" not in event
    ):
        return {}
    response = game_table.get_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]}
    )
    if response["Item"]["game_state"] != "LOBBY":
        return {}
    players_info = response["Item"]["players"]
    if event["player_id"] not in players_info:
        return {}
    chosen_throne_room_ids = set()
    for player_id in players_info:
        if "throne_room_id" in players_info[player_id]:
            throne_room_id = players_info[player_id]["throne_room_id"]
            chosen_throne_room_ids.add(throne_room_id)

    if event["throne_room_id"] in chosen_throne_room_ids:
        return {}
    players_info[event["player_id"]]["throne_room_id"] = event[
        "throne_room_id"
    ]
    game_table.update_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]},
        UpdateExpression="SET players = :updated_players",
        ExpressionAttributeValues={":updated_players": players_info},
    )
    return {
        "player_id": event["player_id"],
        "game_id": event["game_id"],
        "game_timestamp": event["game_timestamp"],
    }


def modify_lobby(event) -> Dict[str, str]:
    if (
        "game_id" not in event
        or "game_timestamp" not in event
        or "player_id" not in event
        or "num_disasters" not in event
        or "num_catastrophes" not in event
        or "num_safe" not in event
    ):
        return {}
    response = game_table.get_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]}
    )
    if response["Item"]["game_state"] != "LOBBY":
        return {}
    players_info = response["Item"]["players"]
    if event["player_id"] not in players_info:
        return {}
    game_table.update_item(
        Key={"id": event["game_id"], "timestamp": event["game_timestamp"]},
        UpdateExpression="SET num_disasters = :disasters, \
                              num_catastrophes = :catastrophes, \
                              num_safe = :safe",
        ExpressionAttributeValues={
            ":disasters": event["num_disasters"],
            ":catstrophes": event["num_catastrophes"],
            ":safe": event["num_safe"],
        },
    )
    return {
        "player_id": event["player_id"],
        "game_id": event["game_id"],
        "game_timestamp": event["game_timestamp"],
    }


def join_lobby(event) -> Dict[str, str]:
    if "game_id" not in event or "username" not in event:
        return {}
    game_id = event["game_id"]
    response = game_table.query(KeyConditionExpression=Key("id").eq(game_id))
    if (
        len(response["Items"]) == 0
        or response["Items"][0]["game_state"] != "LOBBY"
    ):
        return {}
    timestamp = response["Items"][0]["timestamp"]

    player_id = str(uuid.uuid4())
    username = event["username"]

    updated_players = response["Items"][0]["players"]
    updated_players[player_id] = {"username": username}

    game_table.update_item(
        Key={"id": game_id, "timestamp": timestamp},
        UpdateExpression="SET players = :updated_players",
        ExpressionAttributeValues={":updated_players": updated_players},
    )

    return {
        "player_id": player_id,
        "game_id": game_id,
        "game_timestamp": timestamp,
    }


def create_lobby(event) -> Dict[str, str]:
    if "username" not in event:
        return {}
    game_id = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    player_id = str(uuid.uuid4())
    game_table.put_item(
        Item={
            "id": game_id,
            "timestamp": timestamp,
            "players": {player_id: {"username": event["username"]}},
            "game_state": "LOBBY",
            "num_disasters": NUM_DISASTER_DEFAULT,
            "num_catastrophes": NUM_CATASTROPHES_DEFAULT,
            "num_safe": NUM_SAFE_DEFAULT,
        }
    )
    return {
        "player_id": player_id,
        "game_id": game_id,
        "game_timestamp": timestamp,
    }


def update_game(
    game_id: str, timestamp: int, game_info: Game, game_state: str
):
    game_json = game_info.to_json_obj()
    game_table.update_item(
        Key={"id": game_id, "timestamp": timestamp},
        UpdateExpression="SET game_state = :new_state, \
                              current_disasters = :c_disasters, \
                              previous_disasters = :p_disasters, \
                              players = :players_info, \
                              turn_order = :t_order, \
                              turn_index = :t_index, \
                              shop = :game_shop, \
                              discard = :game_discard, \
                              deck = :game_deck",
        ExpressionAttributeValues={
            ":new_state": game_state,
            ":c_disasters": game_json["current_disasters"],
            ":p_disasters": game_json["previous_disasters"],
            ":players_info": game_json["players"],
            ":t_order": game_json["turn_order"],
            ":t_index": game_json["turn_index"],
            ":game_shop": game_json["shop"],
            ":game_discard": game_json["discard"],
            ":game_deck": game_json["deck"],
        },
    )
