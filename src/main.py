"""main python file"""
from __future__ import annotations
from aux_code.ui import UI
from aux_code.history_system import HistoryEntry
from aux_code.pygame_configure import pygame, draw_hexagon
from aux_code.event_handling import event_handler
from aux_code.constants import SCREEN_SIZES, RECOLOUR_TOOLS, CLICK_TOOLS, LINE_TOOLS
import sys


class Program:
    """main program"""
    ui: UI
    layer: int
    running: bool
    loop_save: dict
    just_finished_drawing: bool
    just_loaded: bool
    file_name: str | None

    def __init__(self, size: tuple[int, int] = (650, 650), canv_size: tuple[int, int] = (65, 65)):
        sys.setrecursionlimit(size[0] * size[1])

        self.ui = UI(screen_size=size, canv_size=canv_size)
        self.layer = 0
        self.file_name = None

        # refresh ui to make everything appear for the first time
        self.ui.refresh_ui()

        # loop savers
        self.running = True
        self.loop_save = {'pixel_history': []}
        self.just_finished_drawing, self.just_loaded = False, False

        # start program
        self.run_program()

        # exit program
        pygame.quit()

    def run_program(self):
        """the main game loop"""
        while self.running:
            x, y = pygame.mouse.get_pos()
            # handle events
            for event in pygame.event.get():
                self.just_finished_drawing, self.just_loaded, self.running = (
                    event_handler(event, self.ui, x, y, self.just_finished_drawing, self.just_loaded,
                                  self.layer, self.running, self.file_name, self.ui.tool.type)
                )
            if self.ui.click_mode:
                self.ui.during_click_mode(x, y)

            # drawing & colouring logistics
            col = self.ui.tool.colour if self.ui.tool.using_main else self.ui.tool.colour2
            alpha = self.ui.tool.alpha if self.ui.tool.using_main else self.ui.tool.alpha2
            if self.ui.canvas.drawing:
                self.drawing_logistics(alpha, col, x, y, self.layer)
            else:
                self.colouring_logistics(alpha, col)

            # redraw
            if self.ui.canvas.needs_redraw:
                if self.just_loaded:
                    self.ui.canvas.redraw_canv(self.ui.screen, force_config=True)
                else:
                    self.ui.canvas.redraw_canv(self.ui.screen, force_config=False)

            # fix history
            if self.just_loaded and len(self.ui.canvas.history) < 1:
                self.ui.canvas.history.past.append(HistoryEntry(self.ui.canvas, 'LOAD'))

            # reset loop variants
            self.just_finished_drawing = False
            self.just_loaded = False

            pygame.display.flip()

    def drawing_logistics(self, alpha, col, x, y, layer):
        """handles drawing stuff"""
        if self.ui.canvas.drawing:
            pixel = self.ui.canvas.pos_gets_pixel(layer, x, y, self.ui.screen)
            self.loop_save['pixel_history'].append(((x, y), pixel))
            fix_pixels = []
            # print(len(self.loop_save['pixel_history']))

            # fixing line skidding (drawing lines between two points in free drawing when moving too fast)
            if self.ui.tool.type in {'PENCIL'} and len(self.loop_save['pixel_history']) > 1:
                pix1, pix2 = self.loop_save['pixel_history'][-2], self.loop_save['pixel_history'][-1]
                if pix1[1] is None or pix2[1] is None or pix1[1] not in pix2[1].adj:
                    fix_pixels = list(
                        self.ui.canvas.get_line(pix1[0], pix2[0], self.ui.canvas.layers[layer][0][0].size, self.ui.screen,
                                                layer, col, alpha, self.ui.tool.overwrite, False))
            # applying the tool action
            if pixel or (self.ui.tool.type in LINE_TOOLS and len(self.ui.tool.positions) > 0):
                affected = self.loop_save['pixel_history']
                pix_to_colour, temporary = self.ui.tool.onclick(pixel, self.ui.canvas, self.ui.screen, layer, (x, y),
                                                                self.ui.canvas.layers[layer][0][0].size, col, alpha,
                                                                already_affected=affected)
                self.loop_save['pixels_tobe_coloured'] = pix_to_colour + fix_pixels

                if self.ui.tool.type in RECOLOUR_TOOLS and not temporary:  # if this tool is one that recolours pixels
                    for pix in self.loop_save['pixels_tobe_coloured']:
                        actual_drawn = self.ui.canvas.layers[-1][pix.coord[1]][pix.coord[0]]
                        draw_hexagon(self.ui.screen, actual_drawn.rgb + (actual_drawn.alpha,),
                                     actual_drawn.position, actual_drawn.size)

            # disable drawing mode for click tools (e.g. bucket)
            if self.ui.tool.type in CLICK_TOOLS:
                self.ui.canvas.drawing_mode(False, self.ui.tool)
                self.ui.canvas.history.override(HistoryEntry(self.ui.canvas, self.ui.tool.type))  # fixes an undo/redo related bug

    def colouring_logistics(self, alpha, col):
        """handles actually configuring the drawings onto the canvas when you're done drawing"""
        num_pixels_coloured = 0  # haven't used this variable in any meaningful way yet
        if self.ui.tool.type in RECOLOUR_TOOLS and 'pixels_tobe_coloured' in self.loop_save:  # if this tool type recolours pixels
            for pix in self.loop_save['pixels_tobe_coloured']:
                pix.recolour(col, alpha, self.ui.tool.overwrite)
                actual_drawn = self.ui.canvas.layers[-1][pix.coord[1]][pix.coord[0]]
                draw_hexagon(self.ui.screen, actual_drawn.rgb + (actual_drawn.alpha,),
                             actual_drawn.position, actual_drawn.size)
                num_pixels_coloured += 1
            self.loop_save['pixels_tobe_coloured'] = []
        self.loop_save['pixel_history'] = []
        if self.just_finished_drawing and num_pixels_coloured > 0:
            # used to be in canv.drawing_mode, but it caused problems since some tools
            # only recolour pixels to canvas after the event calls (in which drawing_mode is called)
            self.ui.canvas.history.override(HistoryEntry(self.ui.canvas, self.ui.tool.type, num_pixels_coloured))


def main(n: int = 17, size=(48, 48)) -> None:
    """test/run the program"""
    Program(SCREEN_SIZES[n], size)


if __name__ == '__main__':
    main(17)
