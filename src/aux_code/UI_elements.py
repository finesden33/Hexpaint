"""UI element classes"""
from __future__ import annotations

from typing import Any
from src.aux_code.extra_functions import hsv_to_rgb, rgb_to_hex
from src.aux_code.pygame_configure import pygame, math, fill_gradient, draw_lines_g, draw_square, draw_text
from src.aux_code.ui import UI  # needed for (host: UI) arg typing
from src.aux_code.constants import COLOUR_UI, HORIZONTAL, VERTICAL


class UIelement:
    """an interactive element in the UI
    this is an ADT superclass"""
    height: int
    width: int
    orientation: str
    images: list[str]
    position: tuple[int, int]
    sing_click: bool
    affect: Any
    etype: str
    host: UI
    hold_val: Any
    label: str

    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int],
                 sing_click: bool, host: UI, etype: str, hold_val: Any, affect: str | None = '', label: str = '') -> None:
        self.height, self.width = height, width
        if self.height == self.width:
            self.orientation = 'square'
        else:
            self.orientation = 'vertical' if self.height > self.width else 'horizontal'
        self.images = images
        self.position = position
        self.sing_click = sing_click
        self.affect = etype if affect == '' else affect
        self.etype = etype
        self.host = host
        self.hold_val = hold_val
        self.label = label

    def rescale(self, height: int, width: int, screen: pygame.Surface) -> None:
        """resize the element (usually happens when esizing the program window"""
        self.height, self.width = height, width
        self.draw(screen)

    def draw(self, screen: pygame.Surface, with_prior: bool = True, from_update: bool = False, image_to_use: int = 0) -> None:
        """draws the element in the pygame window"""
        if with_prior:
            self.draw_prior(screen, from_update)

        if self.images:
            image = pygame.image.load(self.images[image_to_use])
            image = pygame.transform.scale(image, (self.width, self.height))
            screen.blit(image, self.position)

        self.draw_extra(screen)
        if self.label:
            draw_text(screen, (self.position[0], round(self.position[1] - self.height * 1.1)),
                      self.label, font_size=20, col=((0, 0, 0), None))

    def draw_prior(self, screen: pygame.Surface, from_update: bool = False) -> None:
        """draw extra pygame drawings before main images"""
        raise NotImplementedError

    def draw_extra(self, screen: pygame.Surface) -> None:
        """draw extra pygame drawings after main images"""
        raise NotImplementedError

    def mouse_pos(self, mouse_x: float, mouse_y: float) -> tuple[float, float] | None:
        """gets mouse position relative to the element itself (i.e. imagine if the screen was only the size of element
        returns False if your mouse is not on the element"""
        x, y = self.position
        if x < mouse_x < x + self.width and y < mouse_y < y + self.height:
            print("clicked on: " + self.etype)
            return (mouse_x - x, mouse_y - y)
        else:
            return None

    def on_click(self, screen: pygame.Surface, mouse_x: int, mouse_y: int) -> Any:
        """when the mouse is clicking"""
        raise NotImplementedError

    def on_update(self, screen: pygame.Surface, update_value: Any) -> Any:
        """when something else invokes a change (i.e. excluding clicking the element)"""
        self.hold_val = update_value
        self.draw(screen, from_update=True)
        return update_value


class Slider(UIelement):
    """a slider with value range to slide"""
    val_range: tuple[int, int]

    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int],
                 sing_click: bool, etype: str, host: UI, val_range: tuple[int, int],
                 hold_val: Any = None, affect: str | None = '', label: str = '') -> None:
        if hold_val is None:
            hold_val = val_range[0]
        super().__init__(height, width, images, position, sing_click, host, etype, hold_val, affect, label)
        self.val_range = val_range

    def draw_prior(self, screen: pygame.Surface, from_update: bool = False) -> None:
        """draw the background that changes based on current hold_val as well as other vals too"""
        if self.etype in COLOUR_UI:
            ind = 4
            sat_start, sat_end = (hsv_to_rgb(self.host.tool.hue, 0, self.host.tool.velocity),
                                  hsv_to_rgb(self.host.tool.hue, 100, self.host.tool.velocity))
            vel_start, vel_end = ((0, 0, 0), hsv_to_rgb(self.host.tool.hue, self.host.tool.saturation, 100))
            # accessing the other ui element objects we wish to alter
            if not from_update:  # then we should update the other sliders that are related
                sat_bar = self.host.elements['saturation']
                fill_gradient(screen, start_col=sat_start, end_col=sat_end,
                              pos=(math.floor(sat_bar.position[0] + ind), math.floor(sat_bar.position[1] + ind)),
                              width=math.floor(sat_bar.width - ind * 2), height=math.floor(sat_bar.height - ind * 2),
                              vertical=(sat_bar.orientation in VERTICAL), forward=True)
                sat_bar.draw(screen, with_prior=False, from_update=True)  # no priors to avoid infinite loop of accessing eachother
                vel_bar = self.host.elements['velocity']
                fill_gradient(screen, start_col=vel_start, end_col=vel_end,
                              pos=(math.floor(vel_bar.position[0] + ind), math.floor(vel_bar.position[1] + ind)),
                              width=math.floor(vel_bar.width - ind * 2), height=math.floor(vel_bar.height - ind * 2),
                              vertical=(vel_bar.orientation in VERTICAL), forward=True)
                vel_bar.draw(screen, with_prior=False, from_update=True)  # notice how this will call the main draw, then extra draw now

    def draw_extra(self, screen: pygame.Surface) -> None:
        """draws the slider block thing
        """
        ind = ((self.orientation in 'vertical') * self.width + (self.orientation not in 'vertical') * self.height) / 6
        col = (255, 255, 255)

        if self.orientation in HORIZONTAL:
            progress = (self.hold_val / abs(self.val_range[1] - self.val_range[0])) * (self.width - self.height)
            points = [
                (self.position[0] + progress + ind, self.position[1] + ind),
                (self.position[0] + progress + self.height - ind, self.position[1] + ind),
                (self.position[0] + progress + self.height - ind, self.position[1] + self.height - ind),
                (self.position[0] + progress + ind, self.position[1] + self.height - ind)
            ]
            draw_lines_g(screen, col, points, max(2, round(ind * 2)), closed=True)
        elif self.orientation in VERTICAL:
            progress = (self.hold_val / abs(self.val_range[1] - self.val_range[0])) * (self.height - self.width)
            points = [
                (self.position[0] + ind, self.position[1] + progress + ind),
                (self.position[0] - ind, self.position[1] + progress + self.width + ind),
                (self.position[0] + self.width - ind, self.position[1] + progress + self.height - ind),
                (self.position[0] + self.width + ind, self.position[1] + progress - ind)
            ]
            draw_lines_g(screen, col, points, max(2, round(ind * 2)), closed=True)

    def on_click(self, screen: pygame.Surface, mouse_x: int, mouse_y: int) -> Any:
        """input value of attribute of a class you wish to reference, then output the value to use where called"""
        if self.orientation in HORIZONTAL:
            x = max(self.position[0] + self.height / 2, min(mouse_x, self.position[0] + self.width - self.height // 2))
            self.hold_val = math.floor((x - self.position[0] - self.height / 2) /
                                       (self.width - self.height) * abs(self.val_range[1] - self.val_range[0]))
        elif self.orientation in VERTICAL:
            y = max(self.position[1] + self.width / 2, min(mouse_y, self.position[1] + self.height - self.width // 2))
            self.hold_val = math.floor((y - self.position[1] - self.width / 2) /
                                       (self.height - self.width) * abs(self.val_range[1] - self.val_range[0]))
        self.draw(screen)
        return self.hold_val


class Shape(UIelement):
    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int], sing_click: bool, host: UI,
                 etype: str, hold_val: dict, affect: str | None = '', label: str = ''):
        super().__init__(height, width, images, position, sing_click, host, etype, hold_val, affect, label)

    def draw_prior(self, screen: pygame.Surface, from_update: bool = False) -> None:
        """shape border"""
        col = (255, 255, 255) if self.hold_val['colour'] == (0, 0, 0) else (0, 0, 0)
        offset = round(self.width * 0.05)
        new_position = (self.position[0] - offset, self.position[1] - offset)
        draw_square(screen, self.width + offset * 2, new_position, col)

    def draw_extra(self, screen: pygame.Surface) -> None:
        """draw the coloured shape"""
        current_colour = self.hold_val['colour']
        current_hsv = (self.host.tool.hue, self.host.tool.saturation, self.host.tool.velocity)
        text_col = (255, 255, 255) if current_hsv[2] <= 50 else (0, 0, 0)

        draw_square(screen, self.width, self.position, current_colour)
        if self.hold_val['show_info']:
            font_size = max(2, (self.width // 5))
            info = [str(current_colour[0]) + ' ' + str(current_colour[1]) + ' ' + str(current_colour[2]),
                    'hue: ' + str(current_hsv[0]),
                    'sat: ' + str(current_hsv[1]),
                    'vel: ' + str(current_hsv[2]),
                    str(rgb_to_hex(current_colour))]
            init_x, init_y = self.position
            draw_text(screen, (init_x + (font_size // 5) - 1, init_y), info[0],
                      font_size=(font_size - 1), col=(text_col, current_colour))
            for i in range(1, len(info)):
                draw_text(screen, (init_x + font_size // 5, init_y + i * font_size), info[i],
                          font_size=font_size, col=(text_col, current_colour))

    def on_click(self, screen: pygame.Surface, mouse_x: int, mouse_y: int) -> Any:
        """print colour"""
        self.hold_val['show_info'] = not self.hold_val['show_info']
        self.draw(screen)


class Button(UIelement):
    hold_val: bool
    connections: set[str] | None

    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int], host: UI, etype: str,
                 hold_val: Any, affect: str | None = '', label: str = '', connections: set[str] | None = None):
        super().__init__(height, width, images, position, True, host, etype, hold_val, affect, label)
        self.connections = connections

    def draw_prior(self, screen: pygame.Surface, from_update: bool = False) -> None:
        if self.hold_val:
            image = "resources/images/buttonOn.png"
        else:
            image = "resources/images/buttonOff.png"
        image = pygame.image.load(image)
        image = pygame.transform.scale(image, (self.width, self.height))
        screen.blit(image, self.position)

    def draw_extra(self, screen: pygame.Surface) -> None:
        """do nothing"""

    def on_click(self, screen: pygame.Surface, mouse_x: int, mouse_y: int) -> Any:
        """print colour"""
        # note, if the button has no connections, then th following code does nothing
        if self.connections:
            for e in self.host.elements:
                element = self.host.elements[e]
                if element.etype in self.connections and isinstance(element, Button):
                    element.hold_val = False
                    element.draw(screen)
            self.hold_val = True
            self.draw(screen)
            return self.hold_val


class ToggleButton(Button):
    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int], host: UI, etype: str,
                 hold_val: Any, affect: str | None = '', label: str = ''):
        super().__init__(height, width, images, position, host, etype, hold_val, affect, label)

    def on_click(self, screen: pygame.Surface, mouse_x: int, mouse_y: int) -> Any:
        self.hold_val = not self.hold_val
        self.draw(screen)
        return self.hold_val


class ClickButton(Button):
    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int], host: UI, etype: str,
                 hold_val: Any, affect: str | None = ''):
        super().__init__(height, width, images, position, host, etype, hold_val, affect)

    def on_click(self, screen: pygame.Surface, mouse_x: int, mouse_y: int) -> Any:
        # self.hold_val = True
        # return self.hold_val
        raise NotImplementedError

    def when_done(self):
        """when the function call is done"""
        # eval(self.affect)
        # self.hold_val = False
        raise NotImplementedError
