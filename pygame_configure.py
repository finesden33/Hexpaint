"""configurations for pygame"""

from __future__ import annotations

import colorsys
import math
import sys
import pygame


def initialize_pygame_window(width: int, height: int) -> pygame.Surface:
    """Initialize and return a new pygame window with the given width and height.

    Preconditions:
    - width >= 1
    - height >= 1
    """
    pygame.display.init()

    screen_w = width
    screen_h = height
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE | pygame.HWSURFACE)
    screen.fill((255, 255, 255))  # Fill screen with white
    pygame.display.set_caption("HexPaint")
    pygame.display.flip()
    pygame.event.clear()

    return screen


def screen_as_image(screen: pygame.Surface, canv_place: tuple[int, int, int, int] | None) -> str:
    """saves the current screen (used for line draw also)"""
    if canv_place is None:
        canv_place = (0, 0, screen.get_width(), screen.get_height())
    subsurface = screen.subsurface(pygame.Rect(canv_place[0], canv_place[1], canv_place[2], canv_place[3]))
    pygame.image.save(subsurface, 'temp_images/screenshot.png')
    return 'temp_images/screenshot.png'


def draw_hexagon(screen: pygame.Surface, colour: tuple[int, int, int],
                 point: tuple[float, float], radius: float, real_time: bool = False) -> None:
    """draw a hexagon"""
    vertices = []
    for i in range(6):
        angle = i * math.pi / 3 - (math.pi / 6)
        x = point[0] + radius * math.cos(angle)
        y = point[1] + radius * math.sin(angle)
        vertices.append((x, y))

    pygame.draw.polygon(screen, colour, vertices)
    if real_time:
        pygame.display.flip()


def input_mouse_pygame() -> tuple[int, int]:
    """Wait for the user to click on the pygame window, and return the coordinates of the click position
    after the click occurs.

    The return value is the (x, y) coordinates of the mouse click position.
    """
    pygame.event.clear()
    pygame.event.set_blocked(None)
    pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONUP])
    event = pygame.event.wait()

    if event.type == pygame.MOUSEBUTTONUP:
        return event.pos
    else:
        print('Exiting Pygame window. Please restart the Python console!')
        pygame.display.quit()
        sys.exit(0)


def regular_polygon_vertices(screen_width: int, screen_height: int, radius: int, n: int) -> list[tuple[int, int]]:
    """Return a list of vertices of a regular n-sided polygon (i.e., a polygon with n equal sides).

    The polygon is centred on the midpoint of the screen with the given width and height.
    radius specifies the distance between each vertex and the centre of the polygon.

    Preconditions:
    - screen_width >= 2
    - screen_height >= 2
    - radius >= 1
    - n >= 3
    """
    mid_x = screen_width / 2
    mid_y = screen_height / 2

    return [(round(mid_x + radius * math.cos(2 * math.pi * i / n - math.pi / 2)),
             round(mid_y + radius * math.sin(2 * math.pi * i / n - math.pi / 2)))
            for i in range(0, n)]


def float_to_colour(x: float) -> tuple[int, int, int]:
    """Return an RGB24 colour computed from x.

    Preconditions:
    - 0.0 <= x <= 1.0
    """
    rgb = colorsys.hsv_to_rgb(x, 1.0, 1.0)
    return round(rgb[0] * 255), round(rgb[1] * 255), round(rgb[2] * 255)
