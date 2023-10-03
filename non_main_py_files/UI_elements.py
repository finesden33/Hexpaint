"""UI element classes"""
import math
from typing import Any

from non_main_py_files import extra_functions, pygame_configure
from main import UI
from non_main_py_files.constants import *


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

    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int],
                 sing_click: bool, affect: Any, host: UI, etype: str) -> None:
        self.height, self.width = height, width
        self.orientation = 'vertical' if self.height > self.width else 'horizontal'
        self.images = images
        self.position = position
        self.sing_click = sing_click
        self.affect = affect
        self.etype = etype
        self.host = host

    def rescale(self, height: int, width: int, screen: pygame.Surface) -> None:
        """resize the element (usually happens when esizing the program window"""
        self.height, self.width = height, width
        self.draw(screen)

    def draw(self, screen: pygame.Surface, update_value: Any = None, with_prior: bool = True) -> bool:
        """draws the element in the pygame window"""
        if not self.images:
            return False
        if with_prior:
            self.draw_prior(screen, update_value)

        image = pygame.image.load(self.images[0])
        image = pygame.transform.scale(image, (self.width, self.height))
        screen.blit(image, self.position)

        self.draw_extra(screen, update_value=update_value)
        return True

    def draw_extra(self, screen: pygame.Surface, update_value: Any) -> None:
        """draw extra components after main images"""
        raise NotImplementedError

    def draw_prior(self, screen: pygame.Surface, update_value: Any) -> None:
        """draw extra components before main images"""
        raise NotImplementedError

    def mouse_pos(self, mouse_x: float, mouse_y: float) -> tuple[float, float] | None:
        """gets mouse position relative to the element itself (i.e. imagine if the screen was only the size of element
        returns False if your mouse is not on the element"""
        if self.position[0] / 2 < mouse_x < self.position[0] + self.width and \
           self.position[1] < mouse_y < self.position[1] + self.height:
            return (mouse_x - self.position[0], mouse_y - self.position[1])
        else:
            return None

    def on_click(self, screen: pygame.Surface, mouse_x: int, mouse_y: int) -> Any:
        """when the mouse is clicking"""
        raise NotImplementedError


class Slider(UIelement):
    """a slider with value range to slide"""
    val_range: tuple[int, int]
    hold_val: int

    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int],
                 sing_click: bool, affect: Any, etype: str, host: UI, val_range: tuple[int, int]) -> None:
        super().__init__(height, width, images, position, sing_click, affect, host, etype)

        self.val_range = val_range
        self.hold_val = val_range[0]

    def draw_prior(self, screen: pygame.Surface, update_value: Any) -> None:
        """draw the background that changes based on current hold_val as well as other vals too"""
        ind = 4
        if self.etype in COLOUR_UI:
            sat_start, sat_end = (extra_functions.hsv_to_rgb(self.host.tool.hue, 0, self.host.tool.velocity),
                                  extra_functions.hsv_to_rgb(self.host.tool.hue, 100, self.host.tool.velocity))
            vel_start, vel_end = ((0, 0, 0), extra_functions.hsv_to_rgb(self.host.tool.hue, self.host.tool.saturation, 100))
            # accessing the other ui element objects we wish to alter
            sat_bar = self.host.elements['saturation']
            vel_bar = self.host.elements['velocity']
            pygame_configure.fill_gradient(screen, start_col=sat_start, end_col=sat_end,
                                           pos=(math.floor(sat_bar.position[0] + ind), math.floor(sat_bar.position[1] + ind)),
                                           width=math.floor(sat_bar.width - ind * 2), height=math.floor(sat_bar.height - ind * 2),
                                           vertical=(self.orientation in VERTICAL), forward=True)
            sat_bar.draw(screen, update_value, with_prior=False)  # no priors to avoid infinite loop of accessing eachother
            pygame_configure.fill_gradient(screen, start_col=vel_start, end_col=vel_end,
                                           pos=(math.floor(vel_bar.position[0] + ind), math.floor(vel_bar.position[1] + ind)),
                                           width=math.floor(vel_bar.width - ind * 2), height=math.floor(vel_bar.height - ind * 2),
                                           vertical=(self.orientation in VERTICAL), forward=True)
            vel_bar.draw(screen, update_value, with_prior=False)  # notice how this will call the main draw, then extra draw now

    def draw_extra(self, screen: pygame.Surface, update_value: Any = None) -> None:
        """draws the slider block thing
        """
        ind = ((self.orientation in 'vertical') * self.width + (self.orientation not in 'vertical') * self.height) / 6
        col = (255, 255, 255)

        if update_value:
            self.hold_val = update_value
            print(self.hold_val)
        if self.orientation in HORIZONTAL:
            progress = (self.hold_val / abs(self.val_range[1] - self.val_range[0])) * (self.width - self.height)
            points = [
                (self.position[0] + progress + ind, self.position[1] + ind),
                (self.position[0] + progress + self.height - ind, self.position[1] + ind),
                (self.position[0] + progress + self.height - ind, self.position[1] + self.height - ind),
                (self.position[0] + progress + ind, self.position[1] + self.height - ind)
            ]
            print(points)
            pygame_configure.draw_lines_g(screen, col, points, max(2, round(ind * 2)), closed=True)
        elif self.orientation in VERTICAL:
            progress = (self.hold_val / abs(self.val_range[1] - self.val_range[0])) * (self.height - self.width)
            points = [
                (self.position[0] + ind, self.position[1] + progress + ind),
                (self.position[0] - ind, self.position[1] + progress + self.width + ind),
                (self.position[0] + self.width - ind, self.position[1] + progress + self.height - ind),
                (self.position[0] + self.width + ind, self.position[1] + progress - ind)
            ]
            pygame_configure.draw_lines_g(screen, col, points, max(2, round(ind * 2)), closed=True)

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
