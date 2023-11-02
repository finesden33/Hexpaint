"""constants to be used across all project py files"""
import pygame
import screeninfo

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
HORIZONTAL = {'horiz', 'Horiz', 'Horizontal', 'HORIZONTAL', 'horizontal', 'h', 'H'}
VERTICAL = {'vert', 'vertic', 'vertical', 'Vertical', 'VERTICAL', 'v', 'V'}
COLOUR_UI = {'hue', 'saturation', 'velocity'}
DECIMAL_SLIDERS = {'alpha', 'tolerance'}
TOOL_CONTROLS = {'hue', 'saturation', 'velocity', 'alpha', 'tolerance', 'alpha_dim', 'tool_select', 'alpha_tolerate'}
