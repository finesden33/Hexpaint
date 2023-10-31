"""test file"""

from src import main
import pygame
import math

canv = main.HexCanvas((50, 50))


def test_click():
    """testing the 'mouse click after key ignore' bug"""
    pygame.init()
    # screen = pygame.display.set_mode((400, 400))
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                print("P key pressed")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                print("Left mouse button clicked")
        pygame.display.flip()
    pygame.quit()


def relation_test(coord1: tuple = (2, 2), coord2: tuple = (4, 4)):
    """tests the relation method of Pixel"""
    p1, p2 = main.Pixel(coord1, (0, 0, 0), None), main.Pixel(coord2, (0, 0, 0), None)
    return p1.relation(p2)


def hexagonal_distance(x1, y1, x2, y2):
    """hexagonal distance?"""
    x_dif = abs(x2 - x1)
    y_dif = abs(y2 - y1)
    if (x2 < x1) and (y1 % 2 == 1):
        x_dif = max(0, x_dif - (y_dif + 1) / 2)
    else:
        x_dif = max(0, x_dif - y_dif / 2)

    if x2 > x1:
        return math.ceil(x_dif + y_dif)
    else:
        return math.floor(x_dif + y_dif)
