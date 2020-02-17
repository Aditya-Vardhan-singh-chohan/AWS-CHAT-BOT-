import json
import os
from typing import Callable, Tuple


def all_disasters():
    with open(os.path.join("disastle", "data", "disaster_list.json")) as file:
        disaster_list = json.load(file)
        for name, diamond, cross, moon in disaster_list:
            yield Disaster.make(name, diamond, cross, moon)


def all_catastrophes():
    with open(os.path.join("disastle", "data", "catastrophe_list.json")) as file:
        catastrophe_list = json.load(file)
        for name, diamond, cross, moon in catastrophe_list:
            yield Catastrophe.make(name, diamond, cross, moon)


class Disaster:
    @staticmethod
    def make(name: str, diamond: str, cross: str, moon: str):
        return Disaster(
            name,
            translate_damage(diamond),
            translate_damage(cross),
            translate_damage(moon),
        )

    def __init__(
        self,
        name: str,
        diamond: Callable[[int], int],
        cross: Callable[[int], int],
        moon: Callable[[int], int],
    ):
        self.name = name
        self.diamond = diamond
        self.cross = cross
        self.moon = moon

    def damage(
        self,
        x: int,
        links: Tuple[int, int, int],
        reduction: int = 0,
        multiplier: float = 1,
    ):
        d, c, m = links
        d_damage = self.diamond_damage(x, d, multiplier)
        c_damage = self.cross_damage(x, c, multiplier)
        m_damage = self.moon_damage(x, m, multiplier)
        return (
            d_damage,
            c_damage,
            m_damage,
            max(0, d_damage + c_damage + m_damage - reduction),
        )

    def diamond_damage(self, x: int, link: int, multiplier: float = 1):
        return max(0, self.diamond(x) * multiplier - link)

    def cross_damage(self, x: int, link: int, multiplier: float = 1):
        return max(0, self.cross(x) * multiplier - link)

    def moon_damage(self, x: int, link: int, multiplier: float = 1):
        return max(0, self.moon(x) * multiplier - link)


class Catastrophe(Disaster):
    @staticmethod
    def make(name: str, diamond: str, cross: str, moon: str):
        return Catastrophe(
            name,
            translate_damage(diamond),
            translate_damage(cross),
            translate_damage(moon),
        )

    def __init__(
        self,
        name: str,
        diamond: Callable[[int], int],
        cross: Callable[[int], int],
        moon: Callable[[int], int],
    ):
        Disaster.__init__(self, name, diamond, cross, moon)


def translate_damage(damage: str):
    try:
        int(damage)
        return lambda x: int(damage)
    except ValueError:
        if damage == "x":
            return lambda x: x
        if damage == "1+x":
            return lambda x: 1 + x
        if damage == "2x":
            return lambda x: 2 * x
        raise ValueError(damage + " not a valid disaster damage")
