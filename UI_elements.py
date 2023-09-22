"""UI element classes"""
import pygame
import math
from typing import Any


HORIZONTAL = {'horiz', 'Horiz', 'Horizontal', 'HORIZONTAL', 'horizontal', 'h', 'H'}
VERTICAL = {'vert', 'vertic', 'vertical', 'Vertical', 'VERTICAL', 'v', 'V'}


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

    def __init__(self, height: int, width: int, orientation: str, images: list[str], position: tuple[int, int],
                 sing_click: bool, affect: Any, etype: str) -> None:
        self.height, self.width = height, width
        self.orientation = orientation
        self.images = images
        self.position = position
        self.sing_click = sing_click
        self.affect = affect
        self.etype = etype

    def rescale(self, height: int, width: int, screen: pygame.Surface) -> None:
        """resize the element (usually happens when esizing the program window"""
        self.height, self.width = height, width
        self.draw(screen)

    def draw(self, screen: pygame.Surface, update_value: Any = None) -> bool:
        """draws the element in the pygame window"""
        if not self.images:
            return False
        image = pygame.image.load(self.images[0])
        image = pygame.transform.scale(image, (self.width, self.height))
        screen.blit(image, self.position)

        self.draw_extra(screen, update_value=update_value)
        return True

    def draw_extra(self, screen: pygame.Surface, update_value: Any) -> None:
        """draw extra components"""
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

    def __init__(self, height: int, width: int, orientation: str, images: list[str], position: tuple[int, int],
                 sing_click: bool, affect: Any, etype: str, val_range: tuple[int, int]) -> None:
        super().__init__(height, width, orientation, images, position, sing_click, affect, etype)

        self.val_range = val_range
        self.hold_val = val_range[0]

    def draw_extra(self, screen: pygame.Surface, update_value: Any = None) -> None:
        """draws the slider block thing
        """
        indent = 2.5
        col = (255, 255, 255)
        if update_value:
            self.hold_val = update_value
        if self.orientation in HORIZONTAL:
            progress = (self.hold_val / abs(self.val_range[1] - self.val_range[0])) * (self.width - self.height)
            points = [
                (self.position[0] + progress + indent, self.position[1] + indent),
                (self.position[0] + progress + self.height - indent, self.position[1] + indent),
                (self.position[0] + progress + self.height - indent, self.position[1] + self.height - indent),
                (self.position[0] + progress + indent, self.position[1] + self.height - indent)
            ]
            pygame.draw.lines(screen, col, True, points, width=round(indent*2))
        elif self.orientation in VERTICAL:
            progress = (self.hold_val / abs(self.val_range[1] - self.val_range[0])) * (self.height - self.width)
            points = [
                (self.position[0], self.position[1] + progress),
                (self.position[0], self.position[1] + progress + self.width),
                (self.position[0] + self.width, self.position[1] + progress + self.height),
                (self.position[0] + self.width, self.position[1] + progress)
            ]
            pygame.draw.lines(screen, col, True, points, round(indent*2))

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
