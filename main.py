"""main python file"""

from __future__ import annotations
import random

import extra_functions
from linked_list import LinkedList
import pygame_configure
from extra_functions import *
from save_and_load import *
from constants import *
import UI_elements
import sys

# TODO: understand what the HECK I was thinking when naming those commit messages
# TODO: cut down save file size by ignoring size and position, and handling those after
# TODO: colour indicator element in gui
# TODO: a tool select gui, and more sliders for tool properties
# TODO: gui resizing and malleability functions
# TODO: split tools into individual objects in a separate file, as children of toolbelt
# TODO: line temp draw (makes use of the save_image)
# TODO: Multiprocressing for undo, fill, etc (tools that take a lot of time), and STOP button (to stop an auto draw midway)


class CanvasADT:
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
                # if self.alpha == 0.0:
                #     self.rgb = None  # fully erased
        else:
            self.rgb = colour
            self.alpha = opacity

    def alike(self, other: Pixel, tolerance: float, alpha_tolerate: bool = True,
              relative_rgba: tuple[int | float] | None = None) -> bool:
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
                  screen: pygame.Surface, relative_rgba: tuple[int | float], colour: tuple[int, int, int],
                  opacity: float, overwrite: bool = False, alpha_dim: float = 0.0, tolerance: float = 0.0,
                  alpha_tolerate: bool = True, draw_inloop=False, adj_index: int = 0,
                  spiral: bool = False, keep_mass: bool = False) -> set[Pixel]:
        """colours the adjacent pixels and itself into a certain colour, possibly dminishing alpha affect
        used for antialiasing, bucket-fill, selecting, paint brush, blur, scramble"""
        # global RECURSION_STAT
        # RECURSION_STAT += 1
        # print(RECURSION_STAT)

        if opacity > 0:
            if spiral and self not in visited:
                if self.alpha != opacity or self.rgb != colour:
                    self.recolour(colour, opacity, overwrite)
                    if draw_inloop:
                        actual_drawn = canv.layers[-1][self.coord[1]][self.coord[0]]
                        pygame_configure.draw_hexagon(screen, actual_drawn.rgb + (actual_drawn.alpha,),
                                                      actual_drawn.position, actual_drawn.size)
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
                                                 spiral=spiral, keep_mass=keep_mass)
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
                                pygame_configure.draw_hexagon(screen, actual_drawn.rgb + (actual_drawn.alpha,),
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

    def __str__(self) -> str:
        """prints a list which is the course of actions (from historyEntries)"""
        lst = [x.action for x in self.past.to_list()] + [x.action + '(undid)' for x in self.future.to_list()]
        return ', '.join(lst)

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


class HexCanvas(CanvasADT):
    """the grid where all the pixels live

    Instance Attributes:
        - width: num of pixels horizontally,
        - height: num of pixels vertically
        - grid: a 2d list, where each element is a horizontal row or pixels
        - background: the background colour of the canvas
            (if it's None then it's an empty canvas (this is dif than a white canvas)
        -
    """
    history: History
    drawing: bool
    needs_redraw: bool
    temp_state: list[list[list[Pixel]]]
    show_border: bool
    start_clear: bool

    def __init__(self, size: tuple[int, int] = (100, 100),
                 background: tuple[int, int, int] | None = (255, 255, 255),
                 load_canvas: list[list[Pixel]] | None = None, start_clear: bool = False) -> None:
        self.layers = []
        self.drawing = False
        self.needs_redraw = True
        self.history = History()
        self.temp_state = []
        self.show_border = True
        self.start_clear = start_clear

        if not load_canvas:
            new_grid = []
            for i in range(0, size[1]):  # i.e. each i is a y coord (lower down on grid is a higher y coord)
                row = []
                for j in range(0, size[0]):  # i.e. each j is an x coord (rightward on grid is a higher x coord)
                    if start_clear:
                        new_pixel = Pixel((j, i), background, None, alpha=0.0)
                    else:
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
            # self.history.override(HistoryEntry(self, tool.type))
            tool.positions = []

            # global RECURSION_STAT
            # print(RECURSION_STAT)
            # RECURSION_STAT = 0
            print('finished drawing')

    def undo(self, screen: pygame.Surface) -> None:
        """returns board to a previous state in history"""
        if self.history.travel_back():  # this also mutates the history (in .travel_back() if it's true)
            self.update_canv_version(screen)

    def redo(self, screen: pygame.Surface) -> None:
        """returns board to a future state in history"""
        if self.history.travel_forward():  # this also mutates the history (in .travel_back() if it's true)
            self.update_canv_version(screen)

    def update_canv_version(self, screen: pygame.Surface) -> None:
        """used in undo and redo to update canvas pixels and appearance to that of the new version you undid/redid to"""
        self.temp_state = self.layers
        new_canvas = self.history.get_history_point()

        # check if the new_canvas we're updating to has different pixel size to detect resize
        if new_canvas.layers[0][0][0].size != self.temp_state[0][0][0].size:
            new_canvas.position_pixels(screen)
        self.refresh_self(new_canvas)
        self.needs_redraw = True

    def redraw_canv(self, screen: pygame.Surface, force_config: bool = False) -> None:
        """redraws the entire canvas (avoid using this unless you need to, since it takes time"""
        if self.needs_redraw:  # just to make sure
            for layer in range(0, len(self.layers)):
                for row in range(0, len(self.layers[layer])):
                    for pixel in range(0, len(self.layers[layer][row])):
                        new_pixel = self.layers[layer][row][pixel]
                        old_pixel = None
                        if self.temp_state and len(self.temp_state[layer]) > row and len(self.temp_state[layer][row]) > pixel:
                            old_pixel = self.temp_state[layer][row][pixel]
                        if (not old_pixel or not new_pixel.is_copy(old_pixel)) or force_config:
                            pygame_configure.draw_hexagon(screen, new_pixel.rgb + (new_pixel.alpha,),
                                                          new_pixel.position, new_pixel.size)
        print('redrew canvas')
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

    def load(self, screen: pygame.Surface, use_current: bool = False) -> bool:
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
            else:
                print('failed to load file')
                return False

        self.width, self.height = len(self.layers[0][0]), len(self.layers[0])
        self.position_pixels(screen)
        for row in self.layers[0]:
            for pixel in row:
                self.get_adjacent_pixels(0, pixel.coord, True)
        self.needs_redraw, self.drawing = True, False
        return True


class HistoryEntry(CanvasADT):
    """a node in history"""
    action: str  # most recent tool action performed (that got it to this canvas)
    num_affected: int  # number of pixels that were affected

    def __init__(self, canv: HexCanvas, action: str, num_affected: int = 0) -> None:
        self.width, self.height = canv.width, canv.height
        self.background = canv.background
        self.layers = []
        self.action = action
        self.num_affected = num_affected
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

    hue: int
    saturation: int
    velocity: int

    def __init__(self):
        """create a tool object"""
        self.type = 'PENCIL'
        self.size = 1
        self.colour = (0, 0, 0)
        self.colour2 = (255, 255, 255)
        self.opacity = 1.0
        self.opacity2 = 0.5
        self.using_main = True
        self.hardness = 0.75  # still unused
        self.positions = []
        self.overwrite = False
        self.tolerance = 0.01
        self.alpha_tolerate = True
        self.globally = False
        self.spiral = False
        self.alpha_dim = 0.0  # set to 0 for normal bucket behaviour
        self.keep_mass = True  # if there should be a specific amount of paint based on alpha_diminish

        self.hue, self.saturation, self.velocity = 0, 0, 0

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
                        pygame_configure.draw_hexagon(screen, actual_drawn.rgb + (actual_drawn.alpha,),
                                                      actual_drawn.position, actual_drawn.size)

                    changed = pixel.paint_adj(visited=visited, pix_queue=pix_queue, relative_rgba=original_rgba,
                                              canv=canv, screen=screen, colour=col, opacity=alpha, overwrite=self.overwrite,
                                              alpha_dim=self.alpha_dim, tolerance=self.tolerance,
                                              alpha_tolerate=self.alpha_tolerate, draw_inloop=True, spiral=self.spiral,
                                              keep_mass=self.keep_mass)
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


class UI:
    """the user interface"""
    background: str
    border_cols: tuple[tuple[int, int, int], tuple[int, int, int]]
    canvas: HexCanvas
    screen: pygame.Surface
    tool: ToolBelt
    elements: dict[str, UI_elements.UIelement]
    click_mode: bool
    clicking: UI_elements.UIelement | None

    def __init__(self, screen_size: tuple[int, int], canv_size: tuple[int, int]) -> None:
        self.background = "images/checker_bg.png"
        self.border_cols = ((50, 50, 50), (90, 90, 90))
        self.screen = pygame_configure.initialize_pygame_window(screen_size[0], screen_size[1])
        self.canvas = HexCanvas(canv_size)
        self.tool = ToolBelt()
        self.canvas.position_pixels(self.screen)
        self.canvas.history.past.append(HistoryEntry(self.canvas, 'NEW'))
        self.click_mode = False
        self.clicking = None

        # element generation (note how the key names are the same as the etype
        self.elements = {
            'hue': UI_elements.Slider(height=20, width=250, affect=self.tool.hue,
                                      sing_click=False, images=["images/huebar.png"], position=(20, 20),
                                      val_range=(0, 360), etype='hue', host=self),
            'saturation': UI_elements.Slider(height=20, width=250, affect=self.tool.saturation,
                                             sing_click=False, images=["images/sliderbar.png"], position=(20, 50),
                                             val_range=(0, 100), etype='saturation', host=self),
            'velocity': UI_elements.Slider(height=20, width=250, affect=self.tool.velocity,
                                           sing_click=False, images=["images/sliderbar.png"], position=(20, 80),
                                           val_range=(0, 100), etype='velocity', host=self)
        }
        # assert here (once we made all the UI elements) to enforce a strict naming scheme on elements
        # (due to conditional cases checking for specific names)
        for element in self.elements:
            e = self.elements[element]
            assert e.host is self and e.etype in e.host.elements and e is e.host.elements[e.etype]

    def refresh_ui(self, only_elements: bool = False) -> None:
        """refreshes the UI"""
        if not only_elements:
            # set up background image
            # crop_rect = pygame.Rect(0, 0, 2000, 1000)  # (x, y, width, height)
            editor_bg = pygame.image.load(self.background)  # .subsurface(crop_rect)
            self.screen.blit(editor_bg, (0, 0))
            # set up canvas border
            pix_ref = self.canvas.layers[0][0][0]
            pix_ref2 = self.canvas.layers[0][-1][-1]
            if self.canvas.show_border:
                widths = (100, 200)
                for i in range(2):
                    pygame_configure.draw_hex_border(screen=self.screen, start_pos=pix_ref.position, start_pos2=pix_ref2.position,
                                                     line_thick=self.screen.get_width() // widths[i], colour=self.border_cols[i],
                                                     rows=self.canvas.height, cols=self.canvas.width, radius=pix_ref.size)

        for e in self.elements:
            self.elements[e].draw(self.screen)

        # pygame_configure.draw_hexagon(self.screen, (0, 0, 0) + (0.3,), (99.9, 99.9), 20.0)

    def not_on_canvas(self, mouse_x: float, mouse_y: float) -> bool:
        """returns whether the mouse is currently on hovering the canvas"""
        pix_ref = self.canvas.layers[0][0][0]
        x_in_scope = (pix_ref.position[0] - pix_ref.size * 2 < mouse_x < pix_ref.position[0] +
                      self.canvas.width * pix_ref.size * math.sqrt(3 / 4) * 2)
        y_in_scope = (pix_ref.position[1] - pix_ref.size * 2 < mouse_y < pix_ref.position[1] +
                      self.canvas.height * pix_ref.size * 3 / 2)
        return not (x_in_scope and y_in_scope)

    def during_click_mode(self, x: int, y: int) -> None:
        """what happens when you are clicking (dragging or whatnot) and element"""
        if not self.clicking:  # if we haven't found the element that we're clicking, search for it
            for element in self.elements:
                e = self.elements[element]
                if e.mouse_pos(x, y):  # if we're hovering it
                    self.clicking = e  # then save that element as the one we're dealing with, until click mode is over
            if not self.clicking:  # if we failed to find an element where you clicked
                self.clicking_mode_switch(False)
        else:
            def recolour_action() -> None:
                """helper function"""
                new_col = extra_functions.hsv_to_rgb(self.tool.hue, self.tool.saturation, self.tool.velocity)
                self.tool.change_colour(new_col, self.tool.opacity, True)
            element = self.clicking
            # extra actions based on element type
            if element.etype == 'hue':
                self.tool.hue = element.on_click(self.screen, x, y)
                recolour_action()
            elif self.clicking.etype == 'saturation':
                self.tool.saturation = element.on_click(self.screen, x, y)
                recolour_action()
            elif element.etype == 'velocity':
                self.tool.velocity = element.on_click(self.screen, x, y)
                recolour_action()
            else:
                element.affect = element.on_click(self.screen, x, y)

            if element.sing_click:  # if our element that we're dealing with is a single click element
                self.clicking_mode_switch(False)

    def clicking_mode_switch(self, activation: bool = False):
        """activates/deactivates clicking mode"""
        if activation:
            self.click_mode = True
        else:
            self.click_mode = False
            self.clicking = None

    def update_colour_ui(self, hsv: tuple[int, int, int]) -> None:
        """this was made for the colour picker to update the colour sliders"""
        self.tool.hue, self.tool.saturation, self.tool.velocity = hsv
        print(hsv)
        for element in [x for x in self.elements if x in COLOUR_UI]:
            e = self.elements[element]
            if e.etype == 'hue':
                e.draw(self.screen, hsv[0], with_prior=True)
            elif e.etype == 'saturation':
                e.draw(self.screen, hsv[1], with_prior=True)
            elif e.etype == 'velocity':
                e.draw(self.screen, hsv[2], with_prior=True)
        self.refresh_ui(only_elements=True)


def open_program(size: tuple[int, int] = (650, 650), canv_size: tuple[int, int] = (65, 65)) -> None:
    """starts the program"""
    sys.setrecursionlimit(size[0] * size[1])

    ui = UI(screen_size=size, canv_size=canv_size)
    layer = 0

    # refresh ui to make everything appear for the first time
    ui.refresh_ui()

    # loop savers
    running = True
    loop_save = {'pixel_history': []}
    just_finished_drawing, just_loaded = False, False

    while running:
        x, y = pygame.mouse.get_pos()

        for event in pygame.event.get():

            # quit game
            if event.type == pygame.QUIT:
                running = False

            # resize window
            elif event.type == pygame.VIDEORESIZE:
                ui.canvas.load(ui.screen, use_current=True)
                # background redraw
                ui.refresh_ui()  # this used to be inside the load function before the ui class was made
                just_loaded = True
                print(ui.screen.get_width(), ui.screen.get_height())

            # special ctrl actions
            elif event.type == pygame.KEYDOWN and pygame.key.get_mods() & pygame.KMOD_CTRL and not ui.canvas.drawing:
                if event.key == pygame.K_z:  # undo action
                    ui.canvas.undo(ui.screen)
                elif event.key == pygame.K_y:  # redo action
                    ui.canvas.redo(ui.screen)
                elif event.key == pygame.K_h:  # print the history of actions in the console
                    print(ui.canvas.history)
                elif event.key == pygame.K_s:  # save file
                    ui.canvas.save()
                elif event.key == pygame.K_l:  # load save file
                    if ui.canvas.load(ui.screen):
                        # background redraw
                        ui.refresh_ui()
                        just_loaded = True
                elif event.key == pygame.K_p:  # print screen
                    pygame_configure.screen_as_image(ui.screen, None)
                elif event.key == pygame.K_d:  # manual force redraw canvas
                    ui.canvas.needs_redraw = True
                    ui.canvas.redraw_canv(ui.screen, force_config=True)

            # switch tool (using tool keybinds)
            elif event.type == pygame.KEYDOWN and event.key in KEYBINDS:
                ui.tool.type = KEYBINDS[event.key]

            # randomly change the colour
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RSHIFT:
                ui.tool.colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                ui.update_colour_ui(extra_functions.rgb_to_hsv(ui.tool.colour[0], ui.tool.colour[1], ui.tool.colour[2]))

            # start drawing (depending on the tool type, this may only hold true for one loop (i.e. for single click tools)
            elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                  and not ui.canvas.drawing and not ui.not_on_canvas(x, y) and not ui.click_mode):
                ui.canvas.drawing_mode(True, ui.tool)

            # finish drawing
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and ui.canvas.drawing:
                ui.canvas.drawing_mode(False, ui.tool)
                just_finished_drawing = True

            # colour picker
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                pixel = ui.canvas.pos_gets_pixel(layer, x, y, ui.screen)
                if pixel:
                    prev_tool, ui.tool.type = ui.tool.type, 'COLOUR_PICKER'
                    ui.tool.onclick(pixel, ui.canvas, ui.screen, layer, (x, y), 0)
                    ui.tool.type = prev_tool
                    ui.update_colour_ui(extra_functions.rgb_to_hsv(ui.tool.colour[0], ui.tool.colour[1], ui.tool.colour[2]))

            # UI click element event
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not ui.click_mode and ui.not_on_canvas(x, y):
                ui.clicking_mode_switch(True)

            # UI release click event
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and (ui.click_mode or ui.not_on_canvas(x, y)):
                ui.clicking_mode_switch(False)

        if ui.click_mode:
            ui.during_click_mode(x, y)

        # set correct colour and alpha
        col = ui.tool.colour if ui.tool.using_main else ui.tool.colour2
        alpha = ui.tool.opacity if ui.tool.using_main else ui.tool.opacity2

        # drawing logistics
        if ui.canvas.drawing:
            pixel = ui.canvas.pos_gets_pixel(layer, x, y, ui.screen)
            loop_save['pixel_history'].append(((x, y), pixel))
            fix_pixels = []

            # fixing line skidding (drawing lines between two points in free drawing when moving too fast)
            if ui.tool.type in {'PENCIL'} and len(loop_save['pixel_history']) > 1:
                pix1, pix2 = loop_save['pixel_history'][-2], loop_save['pixel_history'][-1]
                if pix1[1] is None or pix2[1] is None or pix1[1] not in pix2[1].adj:
                    fix_pixels = list(ui.canvas.get_line(pix1[0], pix2[0], ui.canvas.layers[layer][0][0].size, ui.screen,
                                                         layer, col, alpha, ui.tool.overwrite, False))
            # applying the tool action
            if pixel or (ui.tool.type in {'LINE', 'PAINT_LINE'} and len(ui.tool.positions) > 0):
                pix_to_colour, temporary = ui.tool.onclick(pixel, ui.canvas, ui.screen, layer, (x, y),
                                                           ui.canvas.layers[layer][0][0].size)
                loop_save['pixels_tobe_coloured'] = pix_to_colour + fix_pixels

                if ui.tool.type in RECOLOUR_TOOLS and not temporary:  # if this tool is one that recolours pixels
                    for pix in loop_save['pixels_tobe_coloured']:
                        actual_drawn = ui.canvas.layers[-1][pix.coord[1]][pix.coord[0]]
                        pygame_configure.draw_hexagon(ui.screen, actual_drawn.rgb + (actual_drawn.alpha,),
                                                      actual_drawn.position, actual_drawn.size)

            # disable drawing mode for click tools (e.g. bucket)
            if ui.tool.type in CLICK_TOOLS:
                ui.canvas.drawing_mode(False, ui.tool)
                ui.canvas.history.override(HistoryEntry(ui.canvas, ui.tool.type))  # fixes an undo/redo related bug
        else:
            num_pixels_coloured = 0  # haven't used this variable in any meaningful way yet
            if ui.tool.type in RECOLOUR_TOOLS and 'pixels_tobe_coloured' in loop_save:  # if this tool type recolours pixels
                for pix in loop_save['pixels_tobe_coloured']:
                    pix.recolour(col, alpha, ui.tool.overwrite)
                    actual_drawn = ui.canvas.layers[-1][pix.coord[1]][pix.coord[0]]
                    pygame_configure.draw_hexagon(ui.screen, actual_drawn.rgb + (actual_drawn.alpha,),
                                                  actual_drawn.position, actual_drawn.size)
                    num_pixels_coloured += 1
                loop_save['pixels_tobe_coloured'] = []
            loop_save['pixel_history'] = []

            if just_finished_drawing and num_pixels_coloured > 0:
                # used to be in canv.drawing_mode, but it caused problems since some tools
                # only recolour pixels to canvas after the event calls (in which drawing_mode is called)
                ui.canvas.history.override(HistoryEntry(ui.canvas, ui.tool.type, num_pixels_coloured))

        if ui.canvas.needs_redraw:
            if just_loaded:
                ui.canvas.redraw_canv(ui.screen, force_config=True)
            else:
                ui.canvas.redraw_canv(ui.screen, force_config=False)

        if just_loaded and len(ui.canvas.history) < 1:
            ui.canvas.history.past.append(HistoryEntry(ui.canvas, 'LOAD'))
        just_finished_drawing = False
        just_loaded = False

        pygame.display.flip()

    pygame.quit()


def pix_dict_to_pixel(pd: dict) -> Pixel:
    """converts a pixel dictionary to a Pixel object"""
    p = Pixel(pd['coord'],
              pd['rgb'],
              pd['position'],
              pd['size'],
              pd['alpha'])
    p.selected = pd['selected']
    return p


def test(n: int = 17) -> None:
    """test/run the program"""
    open_program(SCREEN_SIZES[n], (48, 48))
