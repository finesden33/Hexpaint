"""for handling different events"""
from __future__ import annotations

from src.aux_code.constants import KEYBINDS
from src.aux_code.ui import UI
from src.aux_code.pygame_configure import pygame, screen_as_image


def event_handler(event: pygame.event, ui: UI, x: int, y: int, just_finished_drawing, just_started_drawing, just_loaded, layer: int,
                  running: bool, file_name: str, save_loop: dict) -> tuple[bool, bool, bool, bool]:
    """handles different events"""
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
            new_file = ui.canvas.save(file_name)
            if new_file:
                file_name = new_file
            print(file_name)
        elif event.key == pygame.K_l:  # load save file
            loaded, new_file = ui.canvas.load(ui.screen)
            if loaded and new_file:
                file_name = new_file
                print(file_name)
                # background redraw
                ui.refresh_ui()
                just_loaded = True
        elif event.key == pygame.K_p:  # print screen
            screen_as_image(ui.screen, None)
        elif event.key == pygame.K_d:  # manual force redraw canvas
            ui.canvas.needs_redraw = True
            ui.canvas.redraw_canv(ui.screen, force_config=True)

    # switch tool (using tool keybinds)
    elif event.type == pygame.KEYDOWN and event.key in KEYBINDS:
        ui.tool.type = KEYBINDS[event.key]
        ui.update_tool_select_ui(ui.tool.type)

    # randomly change the colour
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_RSHIFT:
        ui.tool.rainbow_mode = True

    elif ui.tool.rainbow_mode and event.type == pygame.KEYUP and event.key == pygame.K_RSHIFT:
        ui.tool.rainbow_mode = False

    # start drawing (depending on the tool type, this may only hold true for one loop (i.e. for single click tools)
    elif (((event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or event.type == pygame.FINGERDOWN)
          and not ui.canvas.drawing and (not ui.not_on_canvas(x, y)) # or tool in LINE_TOOLS) TODO?
          and not ui.click_mode):
        ui.canvas.drawing_mode(True, ui.tool)
        just_started_drawing = True

    # finish drawing
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and ui.canvas.drawing:
        ui.canvas.drawing_mode(False, ui.tool)
        just_finished_drawing = True

    # colour picker
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
        pixel = ui.canvas.pos_gets_pixel(layer, x, y, ui.screen)
        if pixel:
            prev_tool, ui.tool.type = ui.tool.type, 'COLOUR_PICKER'
            ui.tool.onclick(pixel, ui.canvas, ui.screen, layer, (x, y), 0, None, None)
            ui.tool.type = prev_tool
            ui.update_colour_ui(ui.tool.colour, ui.tool.alpha)
        else:
            print('No pixel to pick')

    # UI click element event
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not ui.click_mode and ui.not_on_canvas(x, y):
        ui.clicking_mode_switch(True)

    # UI release click event
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and (ui.click_mode or ui.not_on_canvas(x, y)):
        ui.clicking_mode_switch(False)
    return just_finished_drawing, just_started_drawing, just_loaded, running
