from __future__ import annotations

from typing import Any

from src.aux_code.pygame_configure import pygame, math, draw_hexagon
from src.aux_code.extra_functions import cycle_list, colour_add


class Canvas:
    """parent class of HexCanvas and HistoryEntry"""
    width: int
    height: int
    layers: list[list[list[Pixel]]]
    background: tuple[int, int, int] | None

    def get_adjacent_pixels(self, layer: int,
                            coord: tuple[int, int], update: bool = False) -> list[Pixel]:
        """get a pixel's adjacent pixel objects in an already made canvas/historyEntry
        adjacents start from left adjacent pixel then goes around the pixel clockwise

        Preconditions:
            - self.grid[coord[0]][coord[1]] is a valid Pixel
        """
        x, y = coord
        x_range, y_range = self.width - 1, self.height - 1
        if y % 2 == 0:
            pot_adj = [(x - 1, y), (x - 1, y - 1), (x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y + 1)]
        else:
            pot_adj = [(x - 1, y), (x, y - 1), (x + 1, y - 1), (x + 1, y), (x + 1, y + 1), (x, y + 1)]
        act_adj = []

        for adj in pot_adj:
            if 0 <= adj[0] <= x_range and 0 <= adj[1] <= y_range:
                adj_pixel = self.layers[layer][adj[1]][adj[0]]
                act_adj.append(adj_pixel)
        if update:
            self.layers[layer][coord[1]][coord[0]].adj = act_adj
        return act_adj

    def position_pixels(self, screen: pygame.Surface) -> None:
        """assuming a pygame screen has been made, attribute the position for every pixel in a canvas/historyentry"""
        root3 = math.sqrt(3)
        margin_horiz, margin_vert = 0.5, 0.9
        w, h = screen.get_width() * margin_horiz, screen.get_height() * margin_vert
        n, m = self.width, self.height
        r = min(w / (root3 * (n + 0.5)), h / (1.5 * m + 0.5))  # pixel radius
        x_offset = screen.get_width() * (1 - margin_horiz) / 2
        y_offset = screen.get_height() * (1 - margin_vert) / 2

        for layer in range(0, len(self.layers)):
            for i in range(0, m):
                for j in range(0, n):
                    extra_offset = 0.5 if i % 2 == 0 else 1
                    x = r * root3 * (extra_offset + j)
                    y = r * (1 + 1.5 * i)
                    self.layers[layer][i][j].position = (x_offset + x, y_offset + y)
                    self.layers[layer][i][j].size = r


class Pixel:
    """A pixel on the grid

    Instance Attributes:
        - rgb: an RGB tuple. If it's None then it's an 'empty' pixel
        - alpha: alpha percentage
        - coord: x, y coords for the hexagonal grid
        - adj: list of neighbouring pixels
        - position: actual drawn position on pygame canvas (centre of pixel). If it's None then it hasn't been drawn
        - size: actual radius of pixel drawn (affected by zooming)
        - hovered: if pixel is hovered by cursor
    """
    rgb: tuple[int, int, int] | None
    alpha: float
    coord: tuple[int, int]
    adj: list[Pixel]
    position: tuple[float, float] | None
    size: float
    hovered: bool
    selected: bool
    drawn: bool  # if pixel has been drawn during a draw
    coloured: bool  # if pixel has been coloured during a colouring. Useful for when pixels are marked drawn but not coloured
    in_queue: bool  # if pixel is in a queue for colouring


    def __init__(self, coord: tuple[int, int], colour: tuple[int, int, int] | None,
                 pos: tuple[float, float] | None, size: float = 1.0, alpha: float = 1.0) -> None:
        """create a new pixel (when loading grid or erasing)"""
        self.rgb = colour
        self.alpha = alpha
        self.coord = coord
        self.adj = []
        self.position = pos
        self.size = size
        self.hovered = False
        self.selected = False
        self.drawn = False
        self.coloured = False
        self.in_queue = False

    def copy(self) -> Pixel:
        """returns a copy of itself"""
        pix = Pixel(self.coord, self.rgb, self.position, self.size, self.alpha)
        pix.selected = self.selected
        return pix

    def is_copy(self, other: Pixel) -> bool:
        """checks if another Pixel is a copy of itself (used to avoid unecessary redrawing)"""
        return [self.rgb, self.alpha, self.position, self.size, self.selected] == \
            [other.rgb, other.alpha, other.position, other.size, other.selected]

    def set_drawn(self, enforce_drawn_once: bool) -> bool:
        """set pixel as drawn. returns false if pixel has already been drawn, i.e. this is a problem"""
        if enforce_drawn_once:
            if self.drawn:
                return False
            self.drawn = True
        else:
            self.drawn = False
        return True

    def set_undrawn(self) -> None:
        """set pixel as undrawn"""
        self.drawn = False
        # self.coloured will be set to False elsewhere

    def recolour(self, colour: tuple[int, int, int] | None, alpha: float = 1.0, overwrite: bool = False) -> None:
        """recolour a pixel"""
        if not overwrite:
            if colour:
                self.rgb, self.alpha = colour_add(self.rgb, colour, self.alpha, alpha)
            else:  # erase
                self.alpha = max(0.0, self.alpha * (1 - alpha))
                # if self.alpha == 0.0:
                #     self.rgb = None  # fully erased
        else:
            self.rgb = colour
            self.alpha = alpha
        self.coloured = True

    def alike(self, other: Pixel, tolerance: float, alpha_tolerate: bool = True,
              relative_rgba: tuple[int | float] | None = None) -> bool:
        """determines if two pixels have similar colour and alpha given a tolerance
        Note: a tolerance of 0.0 means only pixels with exactly the same colour are alike
        A tolerance of 1.0 means any pixel colour is alike

        The relative_rgba is usually referring to the
        """
        if not relative_rgba:
            relative_rgba = self.rgb + (self.alpha,)
        col_deviation = sum(abs(relative_rgba[i] - other.rgb[i]) for i in range(3)) / 3 / 255
        alpha_deviation = abs(relative_rgba[3] - other.alpha) if alpha_tolerate else 0.0
        return col_deviation <= tolerance ** 2 and alpha_deviation <= tolerance ** 2

    def relation(self, other: Pixel) -> int:
        """how close one pixel is from another, in which self is the centre of a big hexagon,
        and the return value is the size the hexagon needs to be until it contains the other Pixel"""
        x1, y1 = self.coord
        x2, y2 = other.coord
        x_dif, y_dif = abs(x2 - x1), abs(y2 - y1)
        x_dif = max(0.0, (x_dif + (y1 % 2 == 1)) - (y_dif + (y1 % 2 == 1)) / 2)

        if x2 > x1 and y1 % 2 == 0:
            return math.ceil(x_dif + y_dif)
        elif x2 > x1 + (y_dif - 1) / 2 and y1 % 2 == 1 and y2 % 2 == 0:
            return math.ceil(x_dif + y_dif) - 1
        else:
            return math.floor(x_dif + y_dif)

    def paint_adj(self, visited: set[Pixel], pix_queue: list[Pixel], canv: Canvas,
                  screen: pygame.Surface, relative_rgba: tuple[int | float], colour: tuple[int, int, int],
                  alpha: float, overwrite: bool = False, alpha_dim: float = 0.0, tolerance: float = 0.0,
                  alpha_tolerate: bool = True, draw_inloop=False, adj_index: int = 0,
                  spiral: int = 0, keep_mass: bool = False) -> list[Any] | list[tuple[Pixel, tuple[int, int, int, float | Any]]]:
        """colours the adjacent pixels and itself into a certain colour, possibly dminishing alpha affect
        used for antialiasing, bucket-fill, selecting, paint brush, blur, scramble"""
        # global RECURSION_STAT
        # RECURSION_STAT += 1
        # print(RECURSION_STAT)

        if alpha > 0:
            if spiral and self not in visited:
                if self.alpha != alpha or self.rgb != colour:
                    self.recolour(colour, alpha, overwrite)
                    if draw_inloop:
                        actual_drawn = canv.layers[-1][self.coord[1]][self.coord[0]]
                        if actual_drawn.rgb is not None:
                            rgba = actual_drawn.rgb + (actual_drawn.alpha,)
                            draw_hexagon(screen, rgba, actual_drawn.position, actual_drawn.size)
                visited.add(self)
                new_pix_queue = pix_queue + self.adj
                cycle_list(self.adj, adj_index)
                for pix in self.adj:
                    if pix not in visited and pix not in pix_queue:
                        if self.alike(pix, tolerance, alpha_tolerate, relative_rgba):
                            adj_index = (adj_index + 1) % spiral
                            more = pix.paint_adj(visited=visited, pix_queue=new_pix_queue, canv=canv, screen=screen,
                                                 relative_rgba=relative_rgba, colour=colour, alpha=alpha - alpha_dim,
                                                 overwrite=overwrite, alpha_dim=alpha_dim, tolerance=tolerance,
                                                 alpha_tolerate=alpha_tolerate, draw_inloop=draw_inloop, adj_index=adj_index,
                                                 spiral=spiral, keep_mass=keep_mass)
                            visited.update(more)
                return []
            elif not spiral:
                changed = []
                index, curr_alpha = 0, alpha
                while pix_queue and index < len(pix_queue) and curr_alpha > 0:
                    pix = pix_queue[index]
                    # here we use pix_queue as a priority queue as opposed to in spiral mode (opposite use)
                    if self.alike(pix, tolerance, alpha_tolerate, relative_rgba):
                        if not keep_mass:
                            curr_alpha = alpha - self.relation(pix) * alpha_dim
                        else:
                            curr_alpha -= alpha_dim / 10  # TODO: make this 10 be a rate we can change
                        if curr_alpha > 0:
                            for x in pix.adj:
                                if not x.in_queue and x not in visited:
                                    x.in_queue = True
                                    pix_queue.append(x)
                            if pix.alpha != alpha or pix.rgb != colour:
                                # pix.recolour(colour, curr_alpha, overwrite)
                                if draw_inloop:
                                    actual_drawn = canv.layers[-1][pix.coord[1]][pix.coord[0]]
                                    if actual_drawn.rgb is not None:
                                        rgba = actual_drawn.rgb + (actual_drawn.alpha,)
                                        draw_hexagon(screen, rgba, actual_drawn.position, actual_drawn.size)
                                pix_queue.pop(index)
                                pix.in_queue = False
                                changed.append((pix, (colour[0], colour[1], colour[2], curr_alpha)))
                            visited.add(pix)

                    else:
                        index += 1
                return changed
        return []

    def to_dict(self) -> dict:
        """converts pixel object to a dict"""
        mapping = {
            'rgb': self.rgb,
            'alpha': self.alpha,
            'coord': self.coord,
        }
        return mapping
