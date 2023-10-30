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
        assert isinstance(file_contents, str)
        return eval(file_contents)
    else:
        return None


def file_prompt() -> str | None:
    """prompts the user to select a file from their computer, returns the directory"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(initialdir=os.getcwd() + 'resources//save_files', title="Select file",
                                           filetypes=[("Text Files", "*.hexpaint")])
    if file_path.endswith(".hexpaint"):
        return file_path
    else:
        print('Invalid file')


def create_file(lst: list) -> None:
    """saves a list as a txt"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(initialdir=os.getcwd() + 'resources//save_files',
                                             defaultextension=".hexpaint", filetypes=[("Text Files", "*.hexpaint")])
    if file_path:
        with open(file_path, 'w') as file:
            file.write(str(lst))
    else:
        print('failed to save file')
