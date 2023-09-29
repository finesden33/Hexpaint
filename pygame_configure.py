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


def draw_hexagon(screen: pygame.Surface, colour: tuple[int | float] | tuple[int, int, int, float],
                 point: tuple[float, float], radius: float, real_time: bool = False) -> None:
    """draw a hexagon"""
    if len(colour) < 4 or colour[3] > 0.0:
        vertices = []
        for i in range(6):
            angle = i * math.pi / 3 - (math.pi / 6)
            x = point[0] + radius * math.cos(angle)
            y = point[1] + radius * math.sin(angle)
            vertices.append((x, y))

        if len(colour) == 4:
            colour = colour[:3] + (colour[3] * 255,)

        pygame.draw.polygon(screen, colour, vertices)
        if real_time:
            pygame.display.flip()


def draw_g_line(screen: pygame.Surface, colour: tuple[int, int, int], start: tuple[float, float], end: tuple[float, float],
                line_thick: int) -> None:
    """draw a nice line with rounded edges"""
    pygame.draw.line(screen, colour, start, end, line_thick)
    pygame.draw.circle(screen, colour, start, line_thick/2)
    pygame.draw.circle(screen, colour, end, line_thick/2)


def draw_lines_g(screen: pygame.Surface, colour: tuple[int, int, int], verts: list[tuple[int, int]],
                 line_thick: int, closed: bool = True) -> None:
    """draw a nice line with rounded edges"""
    for i in range(0, len(verts) - (not closed)):
        start, end = verts[i], verts[(i + 1) % len(verts)]
        draw_g_line(screen, colour, start, end, line_thick)
    if any(any(i > 300 for i in x) for x in verts):
        print(verts)


def draw_hex_border(screen: pygame.Surface, line_thick: int, start_pos: tuple[float, float], start_pos2: tuple[float, float],
                    rows: int, cols: int, radius: float, colour: tuple[int, int, int] = (100, 100, 100)) -> None:
    """starts at start pos as top left hex, then draws a hex border along the canvas given the radius, rows and cols"""
    for side in range(0, 4):
        hex_width_half = radius * math.sqrt(3 / 4)
        side_len = cols if side % 2 == 0 else rows
        x, y = start_pos
        x2, y2 = start_pos2

        for i in range(0, side_len):
            if side == 0:  # top
                verts = regular_polygon_vertices(x + i * 2 * hex_width_half, y, radius, 6)
                draw_g_line(screen, colour, verts[5], verts[0], line_thick)
                draw_g_line(screen, colour, verts[0], verts[1], line_thick)
            elif side == 1:  # right
                x_extra = (rows % 2 != 0) * hex_width_half  # if there's an even num of rows
                y_shift = i * (3 / 2) * radius
                if i % 2 == 0:
                    verts = regular_polygon_vertices(x2 - hex_width_half + x_extra, y + y_shift, radius, 6)
                    draw_g_line(screen, colour, verts[1], verts[2], line_thick)
                else:
                    verts = regular_polygon_vertices(x2 + x_extra, y + y_shift, radius, 6)
                    draw_g_line(screen, colour, verts[0], verts[1], line_thick)
                    draw_g_line(screen, colour, verts[1], verts[2], line_thick)
                    draw_g_line(screen, colour, verts[2], verts[3], line_thick)
            elif side == 2:  # bottom
                x_extra = (rows % 2 == 0) * hex_width_half  # if there's an even num of rows
                verts = regular_polygon_vertices(x + i * 2 * hex_width_half + x_extra, y2, radius, 6)
                draw_g_line(screen, colour, verts[4], verts[3], line_thick)
                draw_g_line(screen, colour, verts[3], verts[2], line_thick)
            elif side == 3:  # left
                y_shift = i * (3 / 2) * radius
                if i % 2 == 0:
                    verts = regular_polygon_vertices(x, y + y_shift, radius, 6)
                    draw_g_line(screen, colour, verts[5], verts[0], line_thick)
                    draw_g_line(screen, colour, verts[4], verts[5], line_thick)
                    draw_g_line(screen, colour, verts[3], verts[4], line_thick)
                else:
                    verts = regular_polygon_vertices(x + hex_width_half, y + y_shift, radius, 6)
                    draw_g_line(screen, colour, verts[4], verts[5], line_thick)


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


def regular_polygon_vertices(mid_x: float, mid_y: float, radius: float, n: int = 6) -> list[tuple[int, int]]:
    """Return a list of vertices of a regular n-sided polygon (i.e., a polygon with n equal sides).

    The polygon is centred on the midpoint of the screen with the given width and height.
    radius specifies the distance between each vertex and the centre of the polygon.

    Preconditions:
    - radius >= 1
    - n >= 3
    """
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


def fill_gradient(surface: pygame.Surface, start_col: tuple[int, int, int], end_col: tuple[int, int, int], pos: tuple[int, int],
                  height: int, width: int, vertical: bool = True, forward: bool = True):
    """fill a surface with a rectangle gradient pattern
    vertical - should you draw the gradient vertically
    forward - start_col is at left/top

    Pygame recipe: https://www.pygame.org/wiki/GradientCode
    """
    if vertical:
        use = height
    else:
        use = width
    if forward:
        a, b = start_col, end_col
    else:
        b, a = start_col, end_col
    rate = (
        float(b[0] - a[0]) / use,
        float(b[1] - a[1]) / use,
        float(b[2] - a[2]) / use
    )
    if vertical:
        for line in range(pos[1], pos[1] + height):
            color = (
                math.floor(min(max(a[0] + (rate[0] * (line - pos[1])), 0), 255)),
                math.floor(min(max(a[1] + (rate[1] * (line - pos[1])), 0), 255)),
                math.floor(min(max(a[2] + (rate[2] * (line - pos[1])), 0), 255))
            )
            pygame.draw.line(surface, color, (pos[0], line), (pos[0] + width, line))
    else:
        for col in range(pos[0], pos[0] + width):
            color = (
                math.floor(min(max(a[0] + (rate[0] * (col - pos[0])), 0), 255)),
                math.floor(min(max(a[1] + (rate[1] * (col - pos[0])), 0), 255)),
                math.floor(min(max(a[2] + (rate[2] * (col - pos[0])), 0), 255))
            )
            pygame.draw.line(surface, color, (col, pos[1]), (col, pos[1] + height))
