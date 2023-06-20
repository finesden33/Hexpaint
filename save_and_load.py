"""save and load functions"""
import os
import tkinter as tk
from tkinter import filedialog
from typing import Any


def load_file() -> Any:
    """loads a file (prompts user to select, then returns the file contents"""
    selected_file = file_prompt()
    if selected_file:
        with open(selected_file, 'r') as file:
            file_contents = file.read()
        assert type(file_contents) == str
        return eval(file_contents)


def file_prompt() -> str | None:
    """prompts the user to select a file from their computer, returns the directory"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(initialdir=os.getcwd() + '\save_files', title="Select file",
                                           filetypes=[("Text Files", "*.hexpaint")])
    if file_path.endswith(".hexpaint"):
        return file_path
    else:
        print('Invalid file')


def create_file(lst: list) -> None:
    """saves a list as a txt"""
    folder = 'save_files/'
    name = folder + input('File name:')
    name += '.hexpaint'
    if name is None:
        name = 'Untitled'
    with open(name, 'w') as file:
        file.write(str(lst))
    print(f'Saved {name}.txt in the save_files folder')
