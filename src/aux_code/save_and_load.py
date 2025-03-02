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
    output += f'{pix_size},{height},{width}\n\n'
    prev_entry = ''
    all_uniques = set()
    for layer in layers:
        for y in range(height):
            line = ''
            prev_entry = ''
            for x in range(width):
                pixel = layer[y][x]
                if pixel:
                    entry = ''
                    r, g, b = pixel['rgb']
                    a = pixel['alpha']
                    if r == g == b and r in {0, 255} and a == 1:
                        if r == 255:
                            entry += '1'
                        elif r == 0:
                            entry += '0'
                    else:
                        # convert to hex
                        entry += f'{r:02x}{g:02x}{b:02x}'
                        if a != 1:
                            entry += str(int(a * 100))
                        all_uniques.add(entry)
                    # (if it's alpha=1, then we don't need to write it) and we can infer that later in load
                    if prev_entry and prev_entry[0] == '#':
                        count, p_entry = prev_entry.split('-')
                        if entry == p_entry:  # format #45-ff00cc23
                            new_entry = '#' + str(int(count[1:]) + 1) + '-' + p_entry
                            line = line[:len(line) - len(prev_entry) - 1] + new_entry
                            prev_entry = new_entry
                        else:
                            line += entry
                            prev_entry = entry
                    else:
                        if entry == prev_entry:  # format #45-ff00cc23
                            entry = '#2-' + prev_entry
                            line = line[:len(line) - len(prev_entry) - 1] + entry
                            prev_entry = entry
                        else:
                            line += entry
                            prev_entry = entry
                    if x < width - 1:
                        line += ','
            output += line + '\n'
        output += '\n'

    if output[-1] == '\n':
        output = output[:-1]
    return output


def uncompress(file_contents: str) -> list:
    """uncompresses the file contents"""
    layers = []
    file_contents = file_contents.split('\n\n')
    pix_size, width, height = file_contents[0].split(',')
    for i in range(1, len(file_contents)):
        layer = []
        rows = file_contents[i].split('\n')
        for y, row in enumerate(rows):
            if not row:  # if we've reached the end of the layer
                break
            lst = []
            num_in_row_curr = 0
            row_elements = row.split(',')
            row_i = 0
            while row_i < len(row_elements) and num_in_row_curr < int(height):
                pixel = row_elements[row_i]
                count = 1
                if row_elements[row_i][0] == '#':
                    pack = row_elements[row_i].split('-')
                    assert len(pack) == 2
                    count, pixel = int(pack[0][1:]), pack[1]
                if len(pixel) == 1:
                    if pixel == '1':
                        r, g, b = 255, 255, 255
                    else:
                        r, g, b = 0, 0, 0
                    alpha = 1.0
                else:
                    hex_val = pixel[:6]
                    r, g, b = int(hex_val[:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16)
                    alpha = 1.0 if len(pixel) == 6 else int(pixel[6:]) / 100

                for c in range(0, count):
                    lst.append({'rgb': (r, g, b), 'alpha': alpha, 'coord': (num_in_row_curr + c, y)})
                num_in_row_curr += count
                row_i += 1
                if num_in_row_curr > int(height):
                    raise Exception
            if lst:
                layer.append(lst)
                if len(lst) > int(height):
                    print("um yeah lol")
        layers.append(layer)
    return [layers, pix_size]

#
# # huffman encoding
# def encode_colours(file: str, all_uniques: set) -> str:
#     for unique in all_uniques:
#         file = file.replace(unique, f'#{len(unique)}')
#
#     return new_file

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
