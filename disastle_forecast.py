from collections import defaultdict
from math import factorial
from typing import Dict, List, Tuple

from disastle import disasters
from disastle.rooms import Connection


class DisasterForecast:
    def __init__(self, num_disasters: int, num_catastrophes: int):
        self.num_disasters = num_disasters
        self.num_catastrophes = num_catastrophes
        self.prev_disasters: List[str] = []
        self.prev_catastrophes: List[str] = []

    def draw_disaster(self, *name: str):
        self.prev_disasters += list(name)

    def num_disasters_left(self):
        return self.num_disasters - len(self.prev_disasters)

    def num_catastrophes_left(self):
        return self.num_catastrophes - len(self.prev_catastrophes)

    def disasters_prob(self):
        possible_dis = []
        if self.num_disasters_left() > 0:
            for dis in disasters.all_disasters():
                if dis.name not in self.prev_disasters:
                    possible_dis.append(dis)
        possible_catas = []
        if self.num_catastrophes_left() > 0:
            for catas in disasters.all_catastrophes():
                if catas.name not in self.prev_catastrophes:
                    possible_catas.append(catas)
        num_both_dis_catas = self.num_disasters_left() + self.num_catastrophes_left()
        dis_prob = (
            float(self.num_disasters_left() ** 2)
            / (num_both_dis_catas * len(possible_dis))
            if len(possible_dis) > 0
            else 0.0
        )
        catas_prob = (
            float(self.num_catastrophes_left() ** 2)
            / (num_both_dis_catas * len(possible_catas))
            if len(possible_catas) > 0
            else 0.0
        )
        return ((dis_prob, possible_dis), (catas_prob, possible_catas))

    def damage_distribution(
        self, deck: int, links: Tuple[int, int, int], reduction: int = 0,
    ):
        diamond_link, cross_link, moon_link = links
        diamond_damage: Dict[int, float] = defaultdict(lambda: 0.0)
        cross_damage: Dict[int, float] = defaultdict(lambda: 0.0)
        moon_damage: Dict[int, float] = defaultdict(lambda: 0.0)
        total_damage: Dict[int, float] = defaultdict(lambda: 0.0)
        x = len(self.prev_disasters) + len(self.prev_catastrophes)
        draw_distrib = self.disaster_distribution(deck)
        (dis_prob, possible_dis), (catas_prob, possible_catas) = self.disasters_prob()
        for drawn in draw_distrib:
            damage_multiplier = drawn * (drawn + 1) / 2
            dis_draw_chance = (
                draw_distrib[drawn] * dis_prob * drawn / len(possible_dis)
                if len(possible_dis) > 0
                else 0.0
            )
            for dis in possible_dis:
                d_damage, c_damage, m_damage = dis.damage(x, links)
                diamond_damage[d_damage * damage_multiplier] += dis_draw_chance
                cross_damage[c_damage * damage_multiplier] += dis_draw_chance
                moon_damage[m_damage * damage_multiplier] += dis_draw_chance
                total_damage[
                    dis.total_damage(x, links, reduction, damage_multiplier)
                ] += dis_draw_chance
            catas_draw_chance = (
                draw_distrib[drawn] * catas_prob * drawn / len(possible_catas)
                if len(possible_catas) > 0
                else 0.0
            )
            for catas in possible_catas:
                d_damage, c_damage, m_damage = catas.damage(x, links)
                diamond_damage[d_damage] += catas_draw_chance
                cross_damage[c_damage] += catas_draw_chance
                moon_damage[m_damage] += catas_draw_chance
                total_damage[dis.total_damage(x, links, reduction)] += catas_draw_chance
        return (
            to_distribution(diamond_damage),
            to_distribution(cross_damage),
            to_distribution(moon_damage),
            to_distribution(total_damage),
        )

    def expected_damage(
        self, deck: int, links: Tuple[int, int, int], reduction: int = 0
    ):
        diamond, cross, moon, total = self.damage_distribution(deck, links, reduction)
        expected = (
            expected_value(diamond),
            expected_value(cross),
            expected_value(moon),
            expected_value(total),
        )
        return expected

    def disaster_distribution(self, deck: int):
        dis_left = self.num_disasters_left() + self.num_catastrophes_left()
        if dis_left == 0:
            return {0: 1.0}
        no_dis_prob = select_prob(0, 5, dis_left, deck)
        one_dis_prob = select_prob(1, 5, dis_left, deck)
        redeal_prob = 1 - no_dis_prob - one_dis_prob
        result_distribution = defaultdict(lambda: 0.0)
        result_distribution[0] = no_dis_prob
        one_exploding_distribution = exploding_distribution(1, dis_left - 1, deck)
        for e in one_exploding_distribution:
            result_distribution[1 + e] += one_dis_prob * one_exploding_distribution[e]
        redeal_exploding_distribution = exploding_distribution(4, dis_left - 1, deck)
        for e in redeal_exploding_distribution:
            result_distribution[1 + e] += redeal_prob * redeal_exploding_distribution[e]
        return result_distribution


def exploding_distribution(explodes: int, subjects: int, objects: int):
    if objects < subjects:
        raise ValueError("Objects cannot be less than subjects")
    if explodes == 0 or subjects == 0:
        return {0: 1.0}
    if objects == subjects:
        return {subjects: 1.0}
    if explodes == 1:
        result = {}
        for e in range(subjects + 1):
            result[e] = (
                float(objects - subjects)
                * factorial(subjects)
                / factorial(subjects - e)
                * factorial(objects - e - 1)
                / factorial(objects)
            )
        return result
    exploding_pos_counter = {}
    for e in range(min(explodes, subjects)):
        exploding_pos_counter[e] = num_different_positions(e, explodes)
    pos_distribution = to_distribution(exploding_pos_counter)
    result_distribution = defaultdict(lambda: 0.0)
    for e in range(min(explodes, subjects)):
        child_distribution = exploding_distribution(e, subjects - e, objects - explodes)
        for child_e in child_distribution:
            result_distribution[e + child_e] += (
                pos_distribution[e] * child_distribution[child_e]
            )
    return result_distribution


def select_prob(count: int, selects: int, subjects: int, objects: int):
    if count > selects:
        raise ValueError("Cannot count more subjects than selects")
    if objects < subjects:
        raise ValueError("Objects cannot be less than subjects")
    if objects < selects:
        raise ValueError("Objects cannot be less than selects")
    if selects < 0:
        raise ValueError("Selects cannot be negative")
    if selects == 0 or selects - count > objects - subjects:
        return 0
    return (
        float(factorial(subjects))
        / factorial(subjects - count)
        * factorial(objects - selects)
        / factorial(objects)
        * factorial(objects - subjects)
        / factorial(objects - subjects - selects + count)
        * num_different_positions(count, selects)
    )


def num_different_positions(objects: int, slots: int):
    if objects == 0 or slots <= objects:
        return 1
    return factorial(slots) / factorial(slots - objects) / objects


@staticmethod
def disaster_noredeal_prob(dis: int, deck: int, cards: int):
    if cards == 0 or dis == 0 or deck == 0:
        return {0: 1.0}
    result = {1: float(dis) / deck, 0: float(deck - dis) / deck}
    if cards == 1:
        return result
    has_dist_prob = disaster_noredeal_prob(dis - 1, deck - 1, cards - 1)
    no_dist_prob = disaster_noredeal_prob(dis, deck - 1, cards - 1)
    return


def expected_value(distribution: dict):
    return sum([d * distribution[d] for d in distribution])


def to_distribution(population: dict):
    distribution = {}
    total_count = sum([population[key] for key in population])
    for key in population:
        distribution[key] = float(population[key]) / total_count
    return distribution
