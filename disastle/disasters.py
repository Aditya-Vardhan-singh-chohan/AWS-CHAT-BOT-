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

    def damage(self, x: int, links: Tuple[int, int, int]):
        d, c, m = links
        return (
            self.diamond_damage(x, d),
            self.cross_damage(x, c),
            self.moon_damage(x, m),
        )

    def diamond_damage(self, x: int, link: int):
        return max(0, self.diamond(x) - link)

    def cross_damage(self, x: int, link: int):
        return max(0, self.cross(x) - link)

    def moon_damage(self, x: int, link: int):
        return max(0, self.moon(x) - link)

    def total_damage(self, x: int, links: tuple, reduction: int = 0, multiplier=1):
        d_link, c_link, m_link = links
        return max(
            0,
            (
                self.diamond_damage(x, d_link)
                + self.cross_damage(x, c_link)
                + self.moon_damage(x, m_link)
            )
            * multiplier
            - reduction,
        )


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
