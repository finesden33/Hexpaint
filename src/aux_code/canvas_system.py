from __future__ import annotations

from src.aux_code.save_and_load import create_file, load_file
from src.aux_code.extra_functions import hsv_to_rgb
from src.aux_code.history_system import HistoryEntry, History
from src.aux_code.canvas_foundation import Canvas, Pixel
from src.aux_code.pygame_configure import pygame, math, draw_hexagon
from src.aux_code.constants import LINE_TOOLS, TOOLS


class ToolBelt:
    """The type of tool currently in use

    Instance Attributes:
        - type: the name of the tool currently in use
        - size: size of tool (e.g. a size 3 pencil draws a cluster of 7 pixels in size)
        - colour, colour2: colour rgb values of the tool (you can switch between these two, though gradient uses both)
        - alpha, alpha2: same idea as for colour, colour2, but for alpha value (transparency)
        - hardness: given the size, a hardness of 1.0 would be a full 1.0 alpha all around, but with less hardness,
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
    alpha: float
    alpha2: float
    hardness: float
    tolerance: float
    alpha_tolerate: bool
    positions: list[tuple]
    overwrite: bool
    globally: bool
    spiral: int
    alpha_dim: float
    keep_mass: bool

    hue: int
    saturation: int
    velocity: int

    # general settings
    enforce_draw_once: bool
    pick_alpha: bool
    rainbow_mode: bool
    smart_pencil: bool  # algo that ignores misdrawn pixels that would make pencil look bad


    def __init__(self):
        """create a tool object"""
        self.type = 'PENCIL'
        self.size = 1
        self.colour = (0, 0, 0)
        self.colour2 = (255, 255, 255)
        self.alpha = 1.0
        self.alpha2 = 0.5
        self.using_main = True
        self.hardness = 1.0  # still unused
        self.positions = []

        self.overwrite = False
        self.tolerance = 0.15
        self.alpha_tolerate = True
        self.globally = False
        self.spiral = 0  # must be a num from 0 to 6. If it's 0, then it's like spiral is off, and spiral bucket won't apply
        self.alpha_dim = 0.0  # set to 0 for normal bucket behaviour
        self.keep_mass = True  # if there should be a specific amount of paint based on alpha_diminish

        self.hue, self.saturation, self.velocity = 0, 0, 0

        self.enforce_draw_once = True
        self.pick_alpha = False
        self.rainbow_mode = False
        self.smart_pencil = True

    def change_colour(self, rgb: tuple[int, int, int], alpha: float, main_col: bool):
        """updates colour"""
        if main_col:
            self.colour = rgb
            self.alpha = alpha
        else:
            self.colour2 = rgb
            self.alpha2 = alpha

    def update_col_to_hsv(self) -> None:
        """update the colour rgb value to be equivalent to its hsv attributes"""
        new_col = hsv_to_rgb(self.hue, self.saturation, self.velocity)
        self.change_colour(new_col, self.alpha, True)

    def onclick(self, pixel: Pixel, canv: HexCanvas, screen: pygame.Surface,
                layer: int, pos: tuple[int, int], pix_size: float,
                col: tuple[int, int, int] | None, alpha: float | None) -> tuple[list[tuple[Pixel, tuple[int, int, int, float]]], bool]:
        """when the cursor clicked

        returns a tuple containg a list of pixels that require redrawing, and whether they should be drawn on
        a temp temporary layer (e.g. for a line that hasn't been confirmed)

        """
        # col = self.colour if self.using_main else self.colour2
        # alpha = self.alpha if self.using_main else self.alpha2
        if col is None or alpha is None:
            col, alpha = self.colour, self.alpha

        if self.type == 'PENCIL':
            if not pixel.drawn:
                # expected_final_rgba = colour_add(pixel.rgb, col, pixel.alpha, alpha)
                # if colour_add(pixel.rgb, col, pixel.alpha, alpha)[1] * self.hardness < alpha:
                changed = [(pixel, (col[0], col[1], col[2], alpha))]
                if self.size == 3:
                    for pix in pixel.adj:
                        changed.append((pix, (col[0], col[1], col[2], alpha)))
                return changed, False
            return [], False

        elif self.type == 'BUCKET':
            original_rgba = pixel.rgb + (pixel.alpha,)
            if original_rgba != col + (alpha,):
                if self.globally:
                    changed = []
                    for row in canv.layers[layer]:
                        for pix in row:
                            if pix.alike(pix, self.tolerance, self.alpha_tolerate, original_rgba) and \
                               (pix.rgb != col or pix.alpha != alpha):
                                # pix.recolour(col, alpha, self.overwrite)
                                changed.append((pix, (col[0], col[1], col[2], alpha)))
                    return changed, False
                else:
                    original_rgba = pixel.rgb + (pixel.alpha,)
                    if self.spiral:
                        visited, pix_queue = set(), []
                    else:
                        visited, pix_queue = {pixel}, pixel.adj
                        pixel.in_queue = True
                        for pix in pix_queue:
                            pix.in_queue = True
                        # draw the first pixel
                        # pixel.recolour(col, alpha, self.overwrite)
                        # actual_drawn = canv.layers[-1][pixel.coord[1]][pixel.coord[0]]
                        # draw_hexagon(screen, actual_drawn.rgb + (actual_drawn.alpha,),
                        #              actual_drawn.position, actual_drawn.size)

                    changed = pixel.paint_adj(visited=visited, pix_queue=pix_queue, relative_rgba=original_rgba,
                                              canv=canv, screen=screen, colour=col, alpha=alpha, overwrite=self.overwrite,
                                              alpha_dim=self.alpha_dim / 10, tolerance=self.tolerance,
                                              alpha_tolerate=self.alpha_tolerate, draw_inloop=False, spiral=self.spiral,
                                              keep_mass=self.keep_mass)
                    print("done fill algo")
                    pixel.in_queue = False
                    return list(changed) + [(pixel, (col[0], col[1], col[2], alpha))], False
            else:
                return [], False

        elif self.type == 'COLOUR_PICKER':
            if self.using_main:
                self.colour = pixel.rgb
                if self.pick_alpha:
                    self.alpha = pixel.alpha
            else:
                self.colour2 = pixel.rgb
                if self.pick_alpha:
                    self.alpha2 = pixel.alpha

            return [], False

        elif self.type in LINE_TOOLS:
            actual_pos = pixel.position if pixel else pos
            if not self.positions:  # if we haven't saved any coord yet
                self.positions.append(actual_pos)  # save the start vertex
                #print(self.positions)
            elif len(self.positions) > 1:
                if pixel is not None:
                    self.positions[1] = actual_pos
                    line = canv.get_line(self.positions[0], self.positions[1], pixel.size,
                                         screen, layer, col, alpha, self.overwrite, self.type == 'LINE')
                else:
                    self.positions[1] = pos
                    line = canv.get_line(self.positions[0], self.positions[1], pix_size,
                                         screen, layer, col, alpha, self.overwrite, self.type == 'LINE')
                return [x for x in line if (not x[0].drawn and not x[0].coloured and self.enforce_draw_once) or (not self.enforce_draw_once)], self.type == 'LINE'

            else:  # if we haven't added an end point yet (i.e. we only have the start point)
                self.positions.append(actual_pos)
            return [], False

    def change_tool(self, tool_name):
        """switch to specified tool"""
        if tool_name in TOOLS:
            self.type = tool_name
        else:
            raise Exception


class HexCanvas(Canvas):
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
                 layer: int, col: tuple[int, int, int], alpha: float, overwrite: bool, temp: bool = False) -> set[tuple[Pixel, tuple[int, int, int, float]]]:
        """makes a line between two points on a hex canvas, and return a list of every pixel on the line"""
        segment_rate = segment_rate / 2  # to make the line more accurate
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
                line.add((pix, (col[0], col[1], col[2], alpha)))
                # if not temp:
                #     pix.recolour(col, alpha, overwrite)
                # print(col, alpha)

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
            print('undid')
            self.update_canv_version(screen)

    def redo(self, screen: pygame.Surface) -> None:
        """returns board to a future state in history"""
        if self.history.travel_forward():  # this also mutates the history (in .travel_back() if it's true)
            print('redid')
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
                            draw_hexagon(screen, new_pixel.rgb + (new_pixel.alpha,),
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

    def save(self, current_file: str = None) -> str:
        """save the file as a project file (not an export image)"""
        save_file = [[], self.layers[0][0][0].size]
        for layer in self.layers:
            lyr = []
            for row in layer:
                rw = []
                for pix in row:
                    rw.append(pix.to_dict())
                lyr.append(rw)
            save_file[0].append(lyr)
        file_name = create_file(save_file, current_file)
        return file_name

    def load(self, screen: pygame.Surface, use_current: bool = False) -> tuple[bool, str]:
        """loads a valid file to remake the canvas object"""
        file_name = ''
        if not use_current:
            file, file_name = load_file()  # load file is a tuple of layers + a size
            if file:
                lst = []
                new_canvas_layers, size = file
                for layer in new_canvas_layers:
                    lyr = []
                    for row in layer:
                        rw = []
                        for pix_dict in row:
                            pixel = Pixel(pix_dict['coord'], pix_dict['rgb'], None, size=size, alpha=pix_dict['alpha'])
                            rw.append(pixel)
                        lyr.append(rw)
                    lst.append(lyr)
                self.layers = lst
                self.history.wipe()
            else:
                print('failed to load file')
                return False, ''

        self.width, self.height = len(self.layers[0][0]), len(self.layers[0])
        self.position_pixels(screen)
        for row in self.layers[0]:
            for pixel in row:
                self.get_adjacent_pixels(0, pixel.coord, True)
        self.needs_redraw, self.drawing = True, False
        return True, file_name
