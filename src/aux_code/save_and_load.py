"""save and load functions"""
import os
import tkinter as tk
from tkinter import filedialog
from typing import Any
import base64


def hex_to_binary(hex_str: str) -> str:
    """converts a hex string to binary"""
    return bytes.fromhex(hex_str).decode('utf-8')



def load_file() -> tuple[Any, str]:
    """loads a file (prompts user to select, then returns the file contents"""
    selected_file = file_prompt()
    if selected_file:
        with open(selected_file, 'r') as file:
            file_contents = file.read()
        assert isinstance(file_contents, str)
        name = selected_file.split('/')[-1].split('.')[0]
        if file_contents[0] == '[':
            return eval(file_contents), name
        else:
            try:
                return uncompress(file_contents), name
            except Exception as e:
                print('failed to uncompress file due to: ', e)
                return None, ''
    else:
        return None, ''


def file_prompt() -> str | None:
    """prompts the user to select a file from their computer, returns the directory"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(initialdir=os.getcwd() + 'resources/save_files', title="Select file",
                                           filetypes=[("Text Files", "*.hexpaint")])
    if file_path.endswith(".hexpaint"):
        return file_path
    else:
        print('Invalid file')


def create_file(lst: list, current_file: str | None) -> str:
    """saves a list as a txt"""
    root = tk.Tk()
    root.withdraw()
    sugg_file = '' if current_file is None else current_file + '.hexpaint'
    file_path = filedialog.asksaveasfilename(initialdir=os.getcwd() + 'resources/save_files',
                                             defaultextension=".hexpaint", filetypes=[("Text Files", "*.hexpaint")], initialfile=sugg_file)
    if file_path:
        with open(file_path, 'w') as file:
            bin_data = compress_writing(lst)
            file.write(bin_data)
        return file_path.split('/')[-1].split('.')[0]
    else:
        print('failed to save file')
        return ''


def compress_writing(lst: list) -> str:
    """saves a list as a txt"""
    output = ''
    layers, pix_size = lst[0], lst[1]
    height = len(layers[0])
    width = len(layers[0][0])
    output += str(pix_size) + '\n\n'
    for layer in layers:
        for y in range(height):
            for x in range(width):
                pixel = layer[y][x]
                if pixel:
                    r, g, b = pixel['rgb']
                    a = pixel['alpha']
                    if r == g == b and a == 1:
                        if r == 255:
                            output += '1'
                        elif r == 0:
                            output += '0'
                        else:
                            if r < 10:
                                output += '00' + str(r)
                            elif r < 100:
                                output += '0' + str(r)
                            else:
                                output += str(r)
                    else:
                        # for colour in [r, g, b]:
                        #     if colour < 10:
                        #         output += '00' + str(colour)
                        #     elif colour < 100:
                        #         output += '0' + str(colour)
                        #     else:
                        #         output += str(colour)
                        # convert to hex
                        output += f'{r:02x}{g:02x}{b:02x}'
                        if a != 1:
                            output += str(int(a * 100))
                    # (if it's apha=1, then we don't need to write it) and we can infer that later in load
                    if x < width - 1:
                        output += ','
            output += '\n'
        output += '\n'

    if output[-1] == '\n':
        output = output[:-1]
    return output


def uncompress(file_contents: str) -> list:
    """uncompresses the file contents"""
    layers = []
    file_contents = file_contents.split('\n\n')
    pix_size = file_contents[0]
    width, height = 0, 0
    for i in range(1, len(file_contents)):
        layer = []
        rows = file_contents[i].split('\n')
        for y, row in enumerate(rows):
            if not row:  # if we've reached the end of the layer
                break
            lst = []
            for x, pixel in enumerate(row.split(',')):
                if pixel:
                    if len(pixel) == 1:
                        if pixel == '1':
                            r, g, b = 255, 255, 255
                        else:
                            r, g, b = 0, 0, 0
                        alpha = 1.0
                    else:
                        hex_val = pixel[:6]
                        # if any(['' == hex_val[2 * x: 2 * x + 2] for x in range(3)]):
                        #     print(hex_val)
                        r, g, b = int(hex_val[:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16)
                        alpha = 1.0 if len(pixel) == 6 else int(pixel[6:]) / 100
                    lst.append({'rgb': (r, g, b), 'alpha': alpha, 'coord': (x, y)})
                else:
                    continue
            if lst:
                layer.append(lst)
        layers.append(layer)
    return [layers, pix_size]

#
# -2330012231_64_388 => rgb = (233, 1, 223), alpha = 1.0, position = (64, 388)
#
# but we don't need position
#
# -255033044022 => rgb = (255, 33, 44), alpha = 0.22

# an empty line means new layer. all pixels in a row go on the same line sep by -

# no, since - takes up too much memory, we can just have a new line for each pixel, and a new line for each layer


#
#
