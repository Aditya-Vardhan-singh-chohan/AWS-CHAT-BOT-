import svgwrite
from svgwrite.path import Path
from svgwrite.shapes import Circle, Rect, Polygon, Polyline
from svgwrite.container import Group
from disastle.rooms import Room, Connection
from math import sqrt

BLACK = "#000000"
SILVER = "#c0c0c0"
ORANGE = "#ffa500"
GREEN = "#008000"
YELLOW = "#ffff00"
WHITE = "#ffffff"


def render_diamond(center: tuple, r, width):
    x, y = center
    offset = r - width / sqrt(2)
    return Polygon(
        points=[(x, y - offset), (x + offset, y), (x, y + offset), (x - offset, y)],
        stroke=ORANGE,
        stroke_width=width,
    )


def render_cross(center: tuple, r, width):
    x, y = center
    offset = r / sqrt(2)
    return Polyline(
        points=[
            (x - offset, y - offset),
            (x, y),
            (x + offset, y - offset),
            (x, y),
            (x + offset, y + offset),
            (x, y),
            (x - offset, y + offset),
        ],
        stroke=GREEN,
        stroke_width=width,
    )


def render_moon(center: tuple, r, width):
    x, y = center
    moon = Group()
    moon.add(Circle(center, r - width / 2.0, stroke=YELLOW, stroke_width=width))
    moon.add(
        Circle(
            (x + r / 3.0, y - r / 3.0),
            (r - width / 2.0) * sqrt(2.0 / 3),
            stroke=YELLOW,
            stroke_width=width,
        )
    )
    moon.add(
        Circle(
            center,
            r + width * 2.0 / 3,
            stroke=BLACK,
            stroke_width=width * 4.0 / 3,
            fill_opacity=0,
        )
    )
    return moon


def render_connection(connection: Connection, center: tuple):
    group = Group()
    if connection is Connection.NONE:
        return group
    circle = Circle(center=center, r=(45), fill=BLACK, stroke=SILVER, stroke_width=10)
    group.add(circle)
    if connection is Connection.DIAMOND:
        group.add(render_diamond(center, 30, 8))
    elif connection is Connection.CROSS:
        group.add(render_cross(center, 30, 8))
    elif connection is Connection.MOON:
        group.add(render_moon(center, 30, 8))

    return group


def render_room(room: Room):
    ROOM_SIZE = 600
    FRAME_WIDTH = 10

    card = svgwrite.Drawing(
        filename="render/{}.svg".format(room.name), size=(ROOM_SIZE, ROOM_SIZE)
    )

    background = card.rect(insert=(0, 0), size=("100%", "100%"), fill=BLACK)

    frame = card.g(id="frame")

    frame.add(
        card.rect(
            insert=(FRAME_WIDTH / 2.0, FRAME_WIDTH / 2.0),
            size=(ROOM_SIZE - FRAME_WIDTH, ROOM_SIZE - FRAME_WIDTH),
            stroke_width=FRAME_WIDTH,
            stroke=SILVER,
            fill_opacity=0,
        )
    )

    frame.add(render_connection(room.up, (ROOM_SIZE / 2, 40)))
    frame.add(render_connection(room.right, (ROOM_SIZE - 40, ROOM_SIZE / 2)))
    frame.add(render_connection(room.down, (ROOM_SIZE / 2, ROOM_SIZE - 40)))
    frame.add(render_connection(room.left, (40, ROOM_SIZE / 2)))

    card.add(background)
    card.add(frame)

    card.add(
        card.text(
            text=room.name,
            insert=("50%", "25%"),
            text_anchor="middle",
            font_size=48,
            fill=WHITE,
            font_family="Arial",
        )
    )

    card.save(pretty=True)


render_room(Room.make(0, "Test room", "mncd"))
