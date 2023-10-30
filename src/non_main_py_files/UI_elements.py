"""UI element classes"""
import math
from typing import Any

from non_main_py_files.extra_functions import hsv_to_rgb
from non_main_py_files.pygame_configure import fill_gradient, draw_lines_g
from src.main import UI
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
                 sing_click: bool, affect: Any, host: UI, etype: str, hold_val: Any) -> None:
        self.height, self.width = height, width
        self.orientation = 'vertical' if self.height > self.width else 'horizontal'
        self.images = images
        self.position = position
        self.sing_click = sing_click
        self.affect = affect
        self.etype = etype
        self.host = host
        self.hold_val = hold_val

    def rescale(self, height: int, width: int, screen: pygame.Surface) -> None:
        """resize the element (usually happens when esizing the program window"""
        self.height, self.width = height, width
        self.draw(screen)

    def draw(self, screen: pygame.Surface, with_prior: bool = True, from_update: bool = False) -> bool:
        """draws the element in the pygame window"""
        if not self.images:
            return False
        if with_prior:
            self.draw_prior(screen, from_update)

        image = pygame.image.load(self.images[0])
        image = pygame.transform.scale(image, (self.width, self.height))
        screen.blit(image, self.position)

        self.draw_extra(screen)
        return True

    def draw_prior(self, screen: pygame.Surface, from_update: bool = False) -> None:
        """draw extra components before main images"""
        raise NotImplementedError

    def draw_extra(self, screen: pygame.Surface) -> None:
        """draw extra components after main images"""
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

    def on_update(self, screen: pygame.Surface, update_value: Any) -> Any:
        """when something else invokes a change (i.e. excluding clicking the element)"""
        self.hold_val = update_value
        self.draw(screen, from_update=True)
        return update_value


class Slider(UIelement):
    """a slider with value range to slide"""
    val_range: tuple[int, int]
    hold_val: int

    def __init__(self, height: int, width: int, images: list[str], position: tuple[int, int],
                 sing_click: bool, affect: Any, etype: str, host: UI, val_range: tuple[int, int]) -> None:
        super().__init__(height, width, images, position, sing_click, affect, host, etype, hold_val=val_range[0])

        self.val_range = val_range

    def draw_prior(self, screen: pygame.Surface, from_update: bool = False) -> None:
        """draw the background that changes based on current hold_val as well as other vals too"""
        ind = 4
        if self.etype in COLOUR_UI:
            sat_start, sat_end = (hsv_to_rgb(self.host.tool.hue, 0, self.host.tool.velocity),
                                  hsv_to_rgb(self.host.tool.hue, 100, self.host.tool.velocity))
            vel_start, vel_end = ((0, 0, 0), hsv_to_rgb(self.host.tool.hue, self.host.tool.saturation, 100))
            # accessing the other ui element objects we wish to alter
            if not from_update:  # then we should update the other sliders that are related
                sat_bar = self.host.elements['saturation']
                vel_bar = self.host.elements['velocity']
                fill_gradient(screen, start_col=sat_start, end_col=sat_end,
                              pos=(math.floor(sat_bar.position[0] + ind), math.floor(sat_bar.position[1] + ind)),
                              width=math.floor(sat_bar.width - ind * 2), height=math.floor(sat_bar.height - ind * 2),
                              vertical=(sat_bar.orientation in VERTICAL), forward=True)
                sat_bar.draw(screen, with_prior=False, from_update=True)  # no priors to avoid infinite loop of accessing eachother
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
