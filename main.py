"""main python file"""

from __future__ import annotations
from typing import Any, Optional

import pygame
import random
import math
from linked_list import LinkedList
import pygame_configure
from extra_functions import *
from save_and_load import *
import sys
import screeninfo

# TODO: some fatal bug with historyEntry and get_adjacent and loading and undo
# TODO: line temp draw (makes use of the save_image)
# TODO: undo/redo re-load to deal with canvases of dif. resolutions in history (apparent after resizing screen)
# TODO: undo bug removes two at once only for line objects, Bucket draws twice (note the double 'finished drawing' print)
# TODO: Multiprocressing for undo, fill, etc (tools that take a lot of time), and STOP button (to stop an auto draw midway)
# TODO: split tools into individual objects in a separate file, as children of toolbelt
# TODO: properly align canvas & add gui area of screen (adjusts to resizing)
# TODO: colour wheel and sliders in gui, as well as a tool select

TOOLS = {'PENCIL', 'BUCKET', 'LINE', 'PAINT_LINE', 'LASSO', 'RECT_SELECT', 'MAGIC_WAND', 'PAINT_BRUSH', 'COLOUR_PICKER', 'ERASER',
         'HEXAGON', 'SQUARE', 'TEXT', 'ZOOM', 'PAN', 'GRADIENT', 'REPLACE', 'BLUR', 'SCRAMBLE'}
CLICK_TOOLS = {'BUCKET', 'MAGIC_WAND', 'COLOUR_PICKER'}
RECOLOUR_TOOLS = {'PENCIL', 'BUCKET', 'LINE', 'PAINT_LINE', 'PAINT_BRUSH', 'ERASER', 'HEXAGON', 'SQUARE', 'TEXT', 'GRADIENT',
                  'REPLACE', 'BLUR', 'SCRAMBLE'}
KEYBINDS = {pygame.K_p: 'PENCIL', pygame.K_b: 'BUCKET', pygame.K_l: 'LINE', pygame.K_k: 'PAINT_LINE'}
SCREEN_W, SCREEN_H = screeninfo.get_monitors()[0].width, screeninfo.get_monitors()[0].height
SCREEN_SIZES = [(int(SCREEN_W * (x / 100)), int(SCREEN_H * (x / 100))) for x in range(0, 151)
                if int(SCREEN_W * (x / 100)) == float(SCREEN_W * (x / 100)) and
                int(SCREEN_H * (x / 100)) == float(SCREEN_H * (x / 100))]
# RECURSION_STAT = 0


class Pixel:
    """A pixel on the grid

    Instance Attributes:
        - rgb: an RGB tuple. If it's None then it's an 'empty' pixel
        - alpha: opacity percentage
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

    def __init__(self, coord: tuple[int, int], colour: tuple[int, int, int] | None,
                 pos: tuple[float, float] | None, size: float = 1.0, alpha: float = 0.0) -> None:
        """create a new pixel (when loading grid or erasing)"""
        self.rgb = colour
        self.alpha = alpha
        self.coord = coord
        self.adj = []
        self.position = pos
        self.size = size
        self.hovered = False
        self.selected = False

    def copy(self) -> Pixel:
        """returns a copy of itself"""
        pix = Pixel(self.coord, self.rgb, self.position, self.size, self.alpha)
        pix.selected = self.selected
        return pix

    def is_copy(self, other: Pixel) -> bool:
        """checks if another Pixel is a copy of itself (used to avoid unecessary redrawing)"""
        return [self.rgb, self.alpha, self.position, self.size, self.selected] == \
            [other.rgb, other.alpha, other.position, other.size, other.selected]

    def recolour(self, colour: tuple[int, int, int] | None, opacity: float = 1.0, overwrite: bool = False) -> None:
        """recolour a pixel"""
        if not overwrite:
            if colour:
                a1, a2 = self.alpha, opacity
                rgb1, rgb2 = self.rgb, colour

                final_alpha = max(1 - (1 - a1) * (1 - a2), 0.001)

                self.rgb = (min(255, round((rgb1[0] * a1 * (1 - a2) + rgb2[0] * a2) / final_alpha)),
                            min(255, round((rgb1[1] * a1 * (1 - a2) + rgb2[1] * a2) / final_alpha)),
                            min(255, round((rgb1[2] * a1 * (1 - a2) + rgb2[2] * a2) / final_alpha)))
                self.alpha = final_alpha

            else:  # erase
                self.alpha = max(0.0, self.alpha * (1 - opacity))
                if self.alpha == 0.0:
                    self.rgb = None  # fully erased
        else:
            self.rgb = colour
            self.alpha = opacity

    def alike(self, other: Pixel, tolerance: float, alpha_tolerate: bool = True,
              relative_rgba: tuple[int, int, int, int] | None = None) -> bool:
        """determines if two pixels have similar colour and opacity given a tolerance
        Note: a tolerance of 0.0 means only pixels with exactly the same colour are alike
        A tolerance of 1.0 means any pixel colour is alike

        The relative_rgba is usually referring to the
        """
        if not relative_rgba:
            relative_rgba = self.rgb + (self.alpha,)
        col_deviation = sum(abs(relative_rgba[i] - other.rgb[i]) for i in range(3)) / 3 / 255
        alpha_deviation = abs(relative_rgba[3] - other.alpha) if alpha_tolerate else 0.0
        return col_deviation <= tolerance and alpha_deviation <= tolerance

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

    def paint_adj(self, visited: set[Pixel], pix_queue: list, canv: HexCanvas,
                  screen: pygame.Surface, relative_rgba: tuple[int, int, int, int], colour: tuple[int, int, int], opacity: float,
                  overwrite: bool = False, alpha_dim: float = 0.0, tolerance: float = 0.0, alpha_tolerate: bool = True,
                  draw_inloop=False, adj_index: int = 0, spiral: bool = False, keep_mass: bool = False) -> set[Pixel]:
        """colours the adjacent pixels and itself into a certain colour, possibly dminishing alpha affect
        used for anti-aliasing, bucket-fill, selecting, paint brush, blur, scramble"""
        # global RECURSION_STAT
        # RECURSION_STAT += 1
        # print(RECURSION_STAT)

        if opacity > 0:
            if spiral and self not in visited:
                if self.alpha != opacity or self.rgb != colour:
                    self.recolour(colour, opacity, overwrite)
                    if draw_inloop:
                        actual_drawn = canv.layers[-1][self.coord[1]][self.coord[0]]
                        pygame_configure.draw_hexagon(screen, actual_drawn.rgb, actual_drawn.position, actual_drawn.size)
                visited.add(self)
                new_pix_queue = pix_queue + self.adj
                cycle_list(self.adj, adj_index)
                for pix in self.adj:
                    if pix not in visited and pix not in pix_queue:
                        if self.alike(pix, tolerance, alpha_tolerate, relative_rgba):
                            adj_index = (adj_index + 1) % 1
                            more = pix.paint_adj(visited=visited, pix_queue=new_pix_queue, canv=canv, screen=screen,
                                                 relative_rgba=relative_rgba, colour=colour, opacity=opacity - alpha_dim,
                                                 overwrite=overwrite, alpha_dim=alpha_dim, tolerance=tolerance,
                                                 alpha_tolerate=alpha_tolerate, draw_inloop=draw_inloop, adj_index=adj_index,
                                                 spiral=spiral)
                            visited.update(more)
            elif not spiral:
                index, curr_alpha = 0, opacity
                while pix_queue and index < len(pix_queue) and curr_alpha > 0:
                    pix = pix_queue[index]
                    if not keep_mass:
                        curr_alpha = opacity - self.relation(pix) * alpha_dim
                    else:
                        curr_alpha -= alpha_dim / 10
                    # here we use pix_queue as a priority queue as opposed to in spiral mode (opposite use)
                    if pix not in visited and self.alike(pix, tolerance, alpha_tolerate, relative_rgba) and curr_alpha > 0:
                        pix_queue = pix_queue + [x for x in pix.adj if x not in pix_queue and x not in visited]
                        if pix.alpha != opacity or pix.rgb != colour:
                            pix.recolour(colour, curr_alpha, overwrite)
                            if draw_inloop:
                                actual_drawn = canv.layers[-1][pix.coord[1]][pix.coord[0]]
                                pygame_configure.draw_hexagon(screen, actual_drawn.rgb,
                                                              actual_drawn.position, actual_drawn.size)
                            pix_queue.pop(index)
                        visited.add(pix)
                    else:
                        index += 1
        return [] if draw_inloop else visited

    def to_dict(self) -> dict:
        """converts pixel object to a dict"""
        mapping = {
            'rgb': self.rgb,
            'alpha': self.alpha,
            'coord': self.coord,
            'position': self.position,
            'size': self.size,
            'selected': self.selected
        }
        return mapping


class History:
    """keeps track of canvas history
    Note, every node in the history linked list is a HexCanvas object"""
    past: LinkedList
    future: LinkedList

    def __init__(self) -> None:
        """creates a History object"""
        self.past = LinkedList([])
        self.future = LinkedList([])

    def __len__(self) -> int:
        """length of history"""
        return len(self.past) + len(self.future)

    def no_future(self) -> bool:
        """checks if there is only one thing left"""
        return len(self.future) == 0

    def override(self, entry: HistoryEntry) -> None:
        """create a new present item to history and get rid of everything from the saved point onward"""
        self.future = LinkedList([])
        self.past.append(entry)

    def get_history_point(self) -> HistoryEntry:
        """get to the point in history we're at"""
        return self.past[len(self.past) - 1]

    def travel_back(self) -> bool:
        """travel back in history"""
        if len(self.past) >= 2:
            released = self.past.remove_last()
            self.future.insert(0, released)
            return True
        else:
            return False

    def travel_forward(self) -> bool:
        """travel forward in history"""
        if not self.no_future():
            released = self.future.remove_first()
            self.past.append(released)
            return True
        else:
            return False

    def wipe(self) -> None:
        """wipe history"""
        self.past = LinkedList([])
        self.future = LinkedList([])


class HexCanvas:
    """the grid where all the pixels live

    Instance Attributes:
        - width: num of pixels horizontally,
        - height: num of pixels vertically
        - grid: a 2d list, where each element is a horizontal row or pixels
        - background: the background colour of the canvas
            (if it's None then it's an empty canvas (this is dif than a white canvas)
        -
    """
    width: int
    height: int
    layers: list[list[list[Pixel]]]
    background: tuple[int, int, int] | None
    history: History
    drawing: bool
    needs_redraw: bool
    temp_state: list[list[list[Pixel]]]

    def __init__(self, size: tuple[int, int] = (100, 100),
                 background: tuple[int, int, int] | None = (255, 255, 255),
                 load_canvas: list[list[Pixel]] | None = None) -> None:
        self.layers = []
        self.drawing = False
        self.needs_redraw = True
        self.history = History()
        self.temp_state = []

        if not load_canvas:
            new_grid = []
            for i in range(0, size[1]):  # i.e. each i is a y coord (lower down on grid is a higher y coord)
                row = []
                for j in range(0, size[0]):  # i.e. each j is an x coord (rightward on grid is a higher x coord)
                    new_pixel = Pixel((j, i), background, None, alpha=1.0)
                    row.append(new_pixel)
                new_grid.append(row)
            self.layers.append(new_grid)
            self.width = size[0]
            self.height = size[1]
            self.background = background
            # update every pixel's adjacent attribute now that the grid is complete
            for row in self.layers[0]:
                for pixel in row:
                    self.get_adjacent_pixels(0, pixel.coord, True)
        else:
            self.layers.append(load_canvas)
            self.size = (len(load_canvas), len(load_canvas[0]))
            self.background = None

    def get_adjacent_pixels(self, layer: int, coord: tuple[int, int], update: bool = False) -> list[Pixel]:
        """get a pixel's adjacent pixel objects in an already made canvas
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
        """assuming a pygame screen has been made, attribute the position for every pixel"""
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

    def pos_gets_pixel(self, layer: int, x: int, y: int, screen: pygame.Surface) -> Pixel | None:
        """given a position on the canvas, find which hexagon pixel contains it"""
        root3 = math.sqrt(3)
        margin_horiz, margin_vert = 0.5, 0.9
        w, h = screen.get_width() * margin_horiz, screen.get_height() * margin_vert
        n, m = self.width, self.height
        r = min(w / (root3 * (n + 0.5)), h / (1.5 * m + 0.5))  # pixel radius
        x_offset = screen.get_width() * (1 - margin_horiz) / 2
        y_offset = screen.get_height() * (1 - margin_vert) / 2

        prob_y = max(0, math.floor(((y - y_offset) / r - 1) / 1.5))
        extra_offset = 0.5 if prob_y % 2 == 0 else 1
        prob_x = max(0, math.floor(((x - x_offset) / r / root3) - extra_offset))

        if prob_x in range(0, n) and prob_y in range(0, m):
            prob_pixel = self.layers[layer][prob_y][prob_x]
            for pixel in [prob_pixel] + prob_pixel.adj:
                x_dif, y_dif = abs(pixel.position[0] - x), abs(pixel.position[1] - y)

                if x_dif < (root3 * 0.5 * r) and y_dif < (r - x_dif / root3):
                    return pixel

    def canvas_size(self, size: tuple[int, int], orientation: str) -> None:
        """resizes the canvas
        """
        raise NotImplementedError

    def get_line(self, p1: tuple[int, int], p2: tuple[int, int], segment_rate: float, screen: pygame.Surface,
                 layer: int, col: tuple[int, int, int], alpha: float, overwrite: bool, temp: bool = False) -> set[Pixel]:
        """makes a line between two points on a hex canvas, and return a list of every pixel on the line"""
        line = set()
        x1, y1, x2, y2, = p1[0], p1[1], p2[0], p2[1]
        delta_x, delta_y = max(x1, x2) - min(x2, x1), y2 - y1
        num_pts = math.floor(math.sqrt(delta_x ** 2 + delta_y ** 2) / segment_rate)
        points_to_check = [p1, p2]
        direction = -1 if x2 < x1 else 1
        for n in range(1, num_pts + 1):  # note that if segment_rate > distance from p1 to p2, then num_pts == 0
            if delta_x != 0:
                x = x1 + n * segment_rate * math.cos(math.atan(delta_y / delta_x)) * direction
                y = y1 + n * segment_rate * math.sin(math.atan(delta_y / delta_x))
            else:  # vertical line
                x = x1
                y = y1 + n * segment_rate * (delta_y / abs(delta_y))

            points_to_check.append((x, y))

        for point in points_to_check:
            pix = self.pos_gets_pixel(layer, math.floor(point[0]), math.floor(point[1]), screen)
            if pix:
                line.add(pix)
                if not temp:
                    pix.recolour(col, alpha, overwrite)

        return line

    def drawing_mode(self, activation: bool, tool: ToolBelt) -> None:
        """activates/deactivates drawing mode"""
        if activation:
            self.drawing = True
            print('started drawing')
        else:
            self.drawing = False
            self.history.override(HistoryEntry(self))
            tool.positions = []

            # global RECURSION_STAT
            # print(RECURSION_STAT)
            # RECURSION_STAT = 0
            print('finished drawing')

    def undo(self) -> None:
        """returns board to a previous state in history"""
        if self.history.travel_back():  # this also mutates the history (in .travel_back() if it's true)
            self.temp_state = self.layers
            new_canvas = self.history.get_history_point()
            self.refresh_self(new_canvas)
            self.needs_redraw = True

    def redo(self) -> None:
        """returns board to a future state in history"""
        if self.history.travel_forward():  # this also mutates the history (in .travel_back() if it's true)
            self.temp_state = self.layers
            new_canvas = self.history.get_history_point()
            self.refresh_self(new_canvas)
            self.needs_redraw = True

    def redraw_canv(self, screen: pygame.Surface) -> None:
        """redraws the entire canvas (avoid using this unless you need to, since it takes time"""
        if self.needs_redraw:  # just to make sure
            for layer in range(0, len(self.layers)):
                for row in range(0, len(self.layers[layer])):
                    for pixel in range(0, len(self.layers[layer][row])):
                        new_pixel = self.layers[layer][row][pixel]
                        old_pixel = None
                        if self.temp_state and len(self.temp_state[layer]) > row and len(self.temp_state[layer][row]) > pixel:
                            old_pixel = self.temp_state[layer][row][pixel]
                        if not old_pixel or not new_pixel.is_copy(old_pixel):
                            pygame_configure.draw_hexagon(screen, new_pixel.rgb, new_pixel.position, new_pixel.size)
        self.needs_redraw = False

    def refresh_self(self, new: HexCanvas | HistoryEntry) -> None:
        """partially reinitializes self (still the same object id though"""
        self.width, self.height = new.width, new.height
        self.background = new.background
        self.layers = []
        for layer in new.layers:
            lyr = []
            for row in layer:
                rw = []
                for pix in row:
                    rw.append(pix.copy())
                lyr.append(rw)
            self.layers.append(lyr)
            for row in self.layers[-1]:
                for pixel in row:
                    self.get_adjacent_pixels(len(self.layers) - 1, pixel.coord, True)

    def save(self) -> None:
        """save the file as a project file (not an export image)"""
        lst = []
        for layer in self.layers:
            lyr = []
            for row in layer:
                rw = []
                for pix in row:
                    rw.append(pix.to_dict())
                lyr.append(rw)
            lst.append(lyr)
        create_file(lst)

    def load(self, screen: pygame.Surface, use_current: bool = False) -> None:
        """loads a valid file to remake the canvas object"""
        if not use_current:
            new_canvas_layers = load_file()
            if new_canvas_layers:
                lst = []
                for layer in new_canvas_layers:
                    lyr = []
                    for row in layer:
                        rw = []
                        for pix in row:
                            pixel = pix_dict_to_pixel(pix)
                            rw.append(pixel)
                        lyr.append(rw)
                    lst.append(lyr)
                self.layers = lst
                self.history.wipe()
                self.history.past.append(HistoryEntry(self))
            else:
                print('failed to load file')
                return

        self.width, self.height = len(self.layers[0][0]), len(self.layers[0])
        self.position_pixels(screen)
        for row in self.layers[0]:
            for pixel in row:
                self.get_adjacent_pixels(0, pixel.coord, True)
        self.needs_redraw, self.drawing = True, False

        # background redraw
        refresh_ui(screen)


class HistoryEntry:
    """a node in history"""
    width: int
    height: int
    layers: list[list[list[Pixel]]]
    background: tuple[int, int, int] | None

    def __init__(self, canv: HexCanvas) -> None:
        self.width, self.height = canv.width, canv.height
        self.background = canv.background
        self.layers = []
        for layer in canv.layers:
            lyr = []
            for row in layer:
                rw = []
                for pix in row:
                    rw.append(pix.copy())
                lyr.append(rw)
            self.layers.append(lyr)
            for row in self.layers[-1]:
                for pixel in row:
                    self.get_adjacent_pixels(len(self.layers) - 1, pixel.coord, True)

    def get_adjacent_pixels(self, layer: int, coord: tuple[int, int], update: bool = False) -> list[Pixel]:
        """get a pixel's adjacent pixel objects in an already made canvas
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


class ToolBelt:
    """The type of tool currently in use

    Instance Attributes:
        - type: the name of the tool currently in use
        - size: size of tool (e.g. a size 3 pencil draws a cluster of 7 pixels in size)
        - colour, colour2: colour rgb values of the tool (you can switch between these two, though gradient uses both)
        - opacity, opacity2: same idea as for colour, colour2, but for alpha value (transparency)
        - hardness: given the size, a hardness of 1.0 would be a full 1.0 opacity all around, but with less hardness,
                    as you deviate from the center of the cursor, the alpha effect on a pixel diminishes
        - tolerance: how similar a rgb+a of a pixel value must be to be considered the 'same' colour
                    (used for bucket and magic wand)
        - positions: for storing a list of coordinate/window positions, e.g. used for line calculations
        - overwrite: whether the tool adds to the current pixel on the layer or overwrites it

    Preconditions:
        - type in TOOLS
    """
    type: str
    size: int
    colour: tuple[int, int, int]
    colour2: tuple[int, int, int]
    opacity: float
    opacity2: float
    hardness: float
    tolerance: float
    alpha_tolerate: bool
    positions: list[tuple]
    overwrite: bool
    globally: bool
    spiral: bool
    alpha_dim: float
    keep_mass: bool

    def __init__(self):
        """create a tool object"""
        self.type = 'PENCIL'
        self.size = 1
        self.colour = (0, 0, 0)
        self.colour2 = (255, 255, 255)
        self.opacity = 1.0
        self.opacity2 = 0.5
        self.using_main = True
        self.hardness = 0.75
        self.positions = []
        self.overwrite = False
        self.tolerance = 0.01
        self.alpha_tolerate = True
        self.globally = False
        self.spiral = False
        self.alpha_dim = 0.1
        self.keep_mass = False

    def change_colour(self, rgb: tuple[int, int, int], alpha: float, main_col: bool):
        """updates colour"""
        if main_col:
            self.colour = rgb
            self.opacity = alpha
        else:
            self.colour2 = rgb
            self.opacity2 = alpha

    def onclick(self, pixel: Pixel, canv: HexCanvas, screen: pygame.Surface,
                layer: int, pos: tuple[int, int], pix_size: float) -> tuple[list[Pixel], bool]:
        """when the cursor clicked

        returns a tuple containg a list of pixels that require redrawing, and whether they should be drawn on
        a temp temporary layer (e.g. for a line that hasn't been confirmed)

        """
        col = self.colour if self.using_main else self.colour2
        alpha = self.opacity if self.using_main else self.opacity2
        if self.type == 'PENCIL':
            changed = [pixel]
            pixel.recolour(col, alpha, self.overwrite)  # update the pixel in the HexCanvas object
            if self.size == 3:
                for pix in pixel.adj:
                    pix.recolour(col, alpha, self.overwrite)
                    changed.append(pix)
            return changed, False

        elif self.type == 'BUCKET':
            original_rgba = pixel.rgb + (pixel.alpha,)
            if original_rgba != col + (alpha,):
                if self.globally:
                    changed = []
                    for row in canv.layers[layer]:
                        for pix in row:
                            if pix.alike(pix, self.tolerance, self.alpha_tolerate, original_rgba) and \
                               (pix.rgb != col or pix.alpha != alpha):
                                pix.recolour(col, alpha, self.overwrite)
                                changed.append(pix)
                    return changed, False
                else:
                    original_rgba = pixel.rgb + (pixel.alpha,)
                    if self.spiral:
                        visited, pix_queue = set(), []
                    else:
                        visited, pix_queue = {pixel}, pixel.adj
                        # draw the first pixel
                        pixel.recolour(col, alpha, self.overwrite)
                        actual_drawn = canv.layers[-1][pixel.coord[1]][pixel.coord[0]]
                        pygame_configure.draw_hexagon(screen, actual_drawn.rgb, actual_drawn.position, actual_drawn.size)

                    changed = pixel.paint_adj(visited=visited, pix_queue=pix_queue, relative_rgba=original_rgba,
                                              canv=canv, screen=screen, colour=col, opacity=alpha, overwrite=self.overwrite,
                                              alpha_dim=self.alpha_dim, tolerance=self.tolerance,
                                              alpha_tolerate=self.alpha_tolerate, draw_inloop=True, spiral=self.spiral)
                    return list(changed), False
            else:
                return [], False

        elif self.type == 'COLOUR_PICKER':
            if self.using_main:
                self.colour, self.opacity = pixel.rgb, pixel.alpha
            else:
                self.colour2, self.opacity2 = pixel.rgb, pixel.alpha
            return [], False

        elif self.type in {'LINE', 'PAINT_LINE'}:
            if not self.positions:  # if we haven't saved any coord yet
                self.positions.append(pixel.position)  # save the start vertex
            elif len(self.positions) > 1:
                if pixel is not None:
                    self.positions[1] = pixel.position
                    line = canv.get_line(self.positions[0], self.positions[1], pixel.size,
                                         screen, layer, col, alpha, self.overwrite, self.type == 'LINE')
                else:
                    self.positions[1] = pos
                    line = canv.get_line(self.positions[0], self.positions[1], pix_size,
                                         screen, layer, col, alpha, self.overwrite, self.type == 'LINE')
                return list(line), self.type == 'LINE'

            else:  # if we haven't added an end point yet
                self.positions.append(pixel.position)
            return [], False


def open_program(size: tuple[int, int] = (650, 650), canv_size: tuple[int, int] = (65, 65),
                 rang: tuple[int, int] = (0, 255)) -> None:
    """starts the program"""
    screen = pygame_configure.initialize_pygame_window(size[0], size[1])
    canv = HexCanvas(canv_size)
    canv.position_pixels(screen)
    canv.history.past.append(HistoryEntry(canv))
    tool = ToolBelt()
    layer = 0

    sys.setrecursionlimit(size[0] * size[1])

    refresh_ui(screen)

    # create the pixels for the first layer grid
    # for row in canv.layers[0]:
    #     for pixel in row:
    #         col = (random.randint(rang[0], rang[1]), random.randint(rang[0], rang[1]), random.randint(rang[0], rang[1]))
    #         pygame_configure.draw_hexagon(screen, col, pixel.position, pixel.size)

    running = True
    loop_save = {'pixel_history': []}

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                canv.load(screen, use_current=True)
            elif event.type == pygame.KEYDOWN and pygame.key.get_mods() & pygame.KMOD_CTRL and not canv.drawing:
                if event.key == pygame.K_z:
                    canv.undo()
                elif event.key == pygame.K_y:
                    canv.redo()
                elif event.key == pygame.K_s:
                    canv.save()
                elif event.key == pygame.K_l:
                    canv.load(screen)
                elif event.key == pygame.K_p:
                    pygame_configure.screen_as_image(screen, None)
            elif event.type == pygame.KEYDOWN and event.key in KEYBINDS:
                tool.type = KEYBINDS[event.key]
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RSHIFT:
                tool.colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                canv.drawing_mode(True, tool)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                canv.drawing_mode(False, tool)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:  # colour picker
                x, y = pygame.mouse.get_pos()
                pixel = canv.pos_gets_pixel(layer, x, y, screen)
                if pixel:
                    prev_tool, tool.type = tool.type, 'COLOUR_PICKER'
                    tool.onclick(pixel, canv, screen, layer, (x, y), 0)
                    tool.type = prev_tool

        col = tool.colour if tool.using_main else tool.colour2
        alpha = tool.opacity if tool.using_main else tool.opacity2

        if canv.drawing:
            x, y = pygame.mouse.get_pos()
            pixel = canv.pos_gets_pixel(layer, x, y, screen)
            loop_save['pixel_history'].append(((x, y), pixel))
            fix_pixels = []

            # fixing line skidding (drawing lines between two points in free drawing when moving too fast)
            if tool.type in {'PENCIL'} and len(loop_save['pixel_history']) > 1:
                pix1, pix2 = loop_save['pixel_history'][-2], loop_save['pixel_history'][-1]
                if pix1[1] is None or pix2[1] is None or pix1[1] not in pix2[1].adj:
                    fix_pixels = list(canv.get_line(pix1[0], pix2[0], canv.layers[layer][0][0].size, screen,
                                                    layer, col, alpha, tool.overwrite, False))

            if pixel or (tool.type in {'LINE', 'PAINT_LINE'} and len(tool.positions) > 0):
                pix_to_colour, temporary = tool.onclick(pixel, canv, screen, layer, (x, y), canv.layers[layer][0][0].size)
                loop_save['pixels_tobe_coloured'] = pix_to_colour + fix_pixels

                if tool.type in RECOLOUR_TOOLS and not temporary:  # if this tool is one that recolours pixels
                    for pix in loop_save['pixels_tobe_coloured']:
                        actual_drawn = canv.layers[-1][pix.coord[1]][pix.coord[0]]
                        pygame_configure.draw_hexagon(screen, actual_drawn.rgb, actual_drawn.position, actual_drawn.size)

            if tool.type in CLICK_TOOLS:
                canv.drawing_mode(False, tool)
        else:
            if tool.type in RECOLOUR_TOOLS and 'pixels_tobe_coloured' in loop_save:  # if this tool is one that recolours pixels
                for pix in loop_save['pixels_tobe_coloured']:
                    pix.recolour(col, alpha, tool.overwrite)
                    actual_drawn = canv.layers[-1][pix.coord[1]][pix.coord[0]]
                    pygame_configure.draw_hexagon(screen, actual_drawn.rgb, actual_drawn.position, actual_drawn.size)
                loop_save['pixels_tobe_coloured'] = []
            loop_save['pixel_history'] = []

        if canv.needs_redraw:
            canv.redraw_canv(screen)
        pygame.display.flip()

    pygame.quit()

# test program:
# open_program((650, 650), (40, 40), (255, 255))


def pix_dict_to_pixel(pd: dict) -> Pixel:
    """converts a pixel dictionary to a Pixel object"""
    p = Pixel(pd['coord'],
              pd['rgb'],
              pd['position'],
              pd['size'],
              pd['alpha'])
    p.selected = pd['selected']
    return p


def refresh_ui(screen: pygame.Surface) -> None:
    """refreshes the UI"""

    # crop_rect = pygame.Rect(0, 0, 2000, 1000)  # (x, y, width, height)
    editor_bg = pygame.image.load("images/checker_bg.png")  # .subsurface(crop_rect)
    screen.blit(editor_bg, (0, 0))
    print('Dude, add some UI already')
