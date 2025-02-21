from __future__ import annotations

from src.aux_code.history_system import HistoryEntry
from src.aux_code.canvas_system import HexCanvas, ToolBelt
import src.aux_code.UI_elements as UI_elements
from src.aux_code.pygame_configure import pygame, math, draw_hex_border, initialize_pygame_window
from src.aux_code.extra_functions import rgb_to_hsv
from src.aux_code.constants import TOOLS, TOOL_CONTROLS, DECIMAL_SLIDERS, COLOUR_UI


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
        self.background = "resources/images/checker_bg.png"
        self.border_cols = ((50, 50, 50), (90, 90, 90))
        self.screen = initialize_pygame_window(screen_size[0], screen_size[1])
        self.canvas = HexCanvas(canv_size)
        self.tool = ToolBelt()
        self.canvas.position_pixels(self.screen)
        self.canvas.history.past.append(HistoryEntry(self.canvas, 'NEW'))
        self.click_mode = False
        self.clicking = None

        # element generation (note how the key names are the same as the etype
        slider_size = (20, 250)
        left_start = 20
        top_start = 20
        col_choice_side = round(2.5 * (slider_size[0] + 10))
        y_offset = (10, 30)

        self.elements = {
            'hue': UI_elements.Slider(height=slider_size[0], width=slider_size[1],
                                      sing_click=False, images=["resources/images/huebar.png"],
                                      position=(left_start, top_start),
                                      val_range=(0, 360), etype='hue', host=self),
            'saturation': UI_elements.Slider(height=slider_size[0], width=slider_size[1],
                                             sing_click=False, images=["resources/images/sliderbar.png"],
                                             position=(left_start, top_start + slider_size[0] + y_offset[0]),
                                             val_range=(0, 100), etype='saturation', host=self),
            'velocity': UI_elements.Slider(height=slider_size[0], width=slider_size[1],
                                           sing_click=False, images=["resources/images/sliderbar.png"],
                                           position=(left_start, top_start + 2 * (slider_size[0] + y_offset[0])),
                                           val_range=(0, 100), etype='velocity', host=self),
            'col_choice': UI_elements.Shape(height=col_choice_side, width=col_choice_side, affect=None,
                                            sing_click=True, images=[],
                                            position=(left_start + slider_size[1] + col_choice_side // 5,
                                                      top_start + col_choice_side // 20),
                                            etype='col_choice', host=self, hold_val={'colour': (0, 0, 0), 'show_info': False}),
            'alpha': UI_elements.Slider(height=slider_size[0], width=slider_size[1],
                                        sing_click=False, images=["resources/images/sliderbarSolid.png"],
                                        position=(left_start, top_start + 3 * (slider_size[0] + y_offset[0])),
                                        val_range=(0, 100), etype='alpha', host=self, hold_val=self.tool.alpha * 100),
            'tolerance': UI_elements.Slider(height=slider_size[0], width=slider_size[1],
                                            sing_click=False, images=["resources/images/sliderbarSolid.png"],
                                            position=(left_start, top_start + 4 * (slider_size[0] + y_offset[1])),
                                            val_range=(0, 100), etype='tolerance', host=self, hold_val=self.tool.tolerance * 100,
                                            label='Tolerance'),
            'keep_mass': UI_elements.ToggleButton(height=slider_size[0], width=slider_size[0], images=[],
                                                  position=(left_start, top_start + 5 * (slider_size[0] + y_offset[1])),
                                                  etype='keep_mass', host=self, hold_val=True, label='Keep Fill Mass'),
            'globally': UI_elements.ToggleButton(height=slider_size[0], width=slider_size[0], images=[],
                                                 position=(left_start + (slider_size[0] + 10), top_start + 5 * (slider_size[0] + 10)),
                                                 etype='globally', host=self, hold_val=False, label='Global Fill Mode'),
            'enforce_draw_once': UI_elements.ToggleButton(height=slider_size[0], width=slider_size[0], images=[],
                                                 position=(left_start, top_start + 5 * (slider_size[0] + 10)),
                                                 etype='enforce_draw_once', host=self, hold_val=True, label='Toggle Draw Once Rule'),
            'alpha_dim': UI_elements.Slider(height=slider_size[0], width=slider_size[1],
                                            sing_click=False, images=["resources/images/sliderbarSolid.png"],
                                            position=(left_start, top_start + 6 * (slider_size[0] + y_offset[1])),
                                            val_range=(0, 100), etype='alpha_dim', host=self, hold_val=0.0, label='Alpha Diminish'),
            'PENCIL': UI_elements.Button(height=slider_size[0], width=slider_size[0], images=[], affect="self.tool.change_tool('PENCIL')",
                                         position=(left_start, top_start + 7 * (slider_size[0] + y_offset[1])),
                                         etype='PENCIL', host=self, hold_val=True, label='Pencil', connections=TOOLS),
            'BUCKET': UI_elements.Button(height=slider_size[0], width=slider_size[0], images=[], affect="self.tool.change_tool('BUCKET')",
                                         position=(left_start, top_start + 8 * (slider_size[0] + y_offset[1])),
                                         etype='BUCKET', host=self, hold_val=False, label='Fill', connections=TOOLS),
            'LINE': UI_elements.Button(height=slider_size[0], width=slider_size[0], images=[], affect="self.tool.change_tool('LINE')",
                                       position=(left_start, top_start + 9 * (slider_size[0] + y_offset[1])),
                                       etype='LINE', host=self, hold_val=False, label='Line', connections=TOOLS),
            'PAINT_LINE': UI_elements.Button(height=slider_size[0], width=slider_size[0], images=[],
                                             affect="self.tool.change_tool('PAINT_LINE')",
                                             position=(left_start, top_start + 10 * (slider_size[0] + y_offset[1])),
                                             etype='PAINT_LINE', host=self, hold_val=False, label='Paint Line', connections=TOOLS)
        }
        # assert here (once we made all the UI elements) to enforce a strict naming scheme on elements
        for control in TOOL_CONTROLS:
            assert control in self.elements
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
                    draw_hex_border(screen=self.screen, start_pos=pix_ref.position, start_pos2=pix_ref2.position,
                                                     line_thick=self.screen.get_width() // widths[i], colour=self.border_cols[i],
                                                     rows=self.canvas.height, cols=self.canvas.width, radius=pix_ref.size)

        for e in self.elements:
            if isinstance(e, UI_elements.Button):
                image_choice = int(e.hold_val)  # when true is stored, then we use image 1, i.e. the held down version
            else:
                image_choice = 0
            self.elements[e].draw(self.screen, image_to_use=image_choice)

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
                    break
            if not self.clicking:  # if we failed to find an element where you clicked
                self.clicking_mode_switch(False)
        else:
            element = self.clicking
            if element.etype in TOOLS:
                eval(element.affect)
                element.on_click(self.screen, x, y)
            elif isinstance(element.affect, str):
                # getting target object to affect
                if element.etype in TOOL_CONTROLS:
                    target_obj = self.tool
                else:
                    target_obj = self
                # updating UI and setting values
                if element.etype in DECIMAL_SLIDERS:
                    upload_val = element.on_click(self.screen, x, y) / 100
                else:
                    upload_val = element.on_click(self.screen, x, y)
                if hasattr(target_obj, element.affect):
                    setattr(target_obj, element.affect, upload_val)
            elif element.affect is None:
                element.on_click(self.screen, x, y)

            if element.etype in COLOUR_UI:
                self.tool.update_col_to_hsv()  # note that this updates self.tool.colour
                if 'col_choice' in self.elements:
                    self.elements['col_choice'].on_update(self.screen, {
                        'colour': self.tool.colour,
                        'show_info': self.elements['col_choice'].hold_val['show_info']
                    })

            if element.sing_click:  # if our element that we're dealing with is a single click element
                self.clicking_mode_switch(False)

    def clicking_mode_switch(self, activation: bool = False):
        """activates/deactivates clicking mode"""
        if activation:
            self.click_mode = True
        else:
            self.click_mode = False
            self.clicking = None

    def update_colour_ui(self, colour: tuple[int, int, int], alpha: float = 1.0) -> None:
        """this was made for the colour picker to update the colour sliders"""
        hsv = rgb_to_hsv(colour[0], colour[1], colour[2])
        for element in [x for x in self.elements if x in COLOUR_UI]:
            e = self.elements[element]
            if e.etype == 'hue':
                self.tool.hue = e.on_update(self.screen, hsv[0])
            elif e.etype == 'saturation':
                self.tool.saturation = e.on_update(self.screen, hsv[1])
            elif e.etype == 'velocity':
                self.tool.velocity = e.on_update(self.screen, hsv[2])
        if 'col_choice' in self.elements:
            self.elements['col_choice'].on_update(self.screen, {
                'colour': colour,
                'show_info': self.elements['col_choice'].hold_val['show_info']
            })
        if 'alpha' in self.elements:
            self.elements['alpha'].on_update(self.screen, max(0, min(100, round(alpha * 100))))
            # print(self.tool.alpha)
        self.refresh_ui(only_elements=True)

    def update_tool_select_ui(self, tool_selected: str):
        """updates tool select ui"""
        for element in [x for x in self.elements if x in TOOLS]:
            update_value = element == tool_selected
            self.elements[element].on_update(self.screen, update_value)
