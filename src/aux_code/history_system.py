from __future__ import annotations
from src.aux_code.canvas_foundation import Canvas
from src.aux_code.linked_list import LinkedList


class HistoryEntry(Canvas):
    """a node in history"""
    action: str  # most recent tool action performed (that got it to this canvas)
    num_affected: int  # number of pixels that were affected

    def __init__(self, canv: Canvas, action: str, num_affected: int = 0) -> None:
        self.width, self.height = canv.width, canv.height
        self.background = canv.background
        self.layers = []
        self.action = action
        self.num_affected = num_affected
        for layer in canv.layers:
            lyr = []
            for row in layer:
                rw = []
                for pix in row:
                    rw.append(pix.copy())
                lyr.append(rw)
            self.layers.append(lyr)
            for row in self.layers[-1]:
                for pixel in row:
                    self.get_adjacent_pixels(len(self.layers) - 1, pixel.coord, True)


class History:
    """keeps track of canvas history
    Note, every node in the history linked list is a HexCanvas object"""
    past: LinkedList
    future: LinkedList

    def __init__(self) -> None:
        """creates a History object"""
        self.past = LinkedList([])
        self.future = LinkedList([])

    def __len__(self) -> int:
        """length of history"""
        return len(self.past) + len(self.future)

    def __str__(self) -> str:
        """prints a list which is the course of actions (from historyEntries)"""
        lst = [x.action for x in self.past.to_list()] + [x.action + '(undid)' for x in self.future.to_list()]
        return ', '.join(lst)

    def no_future(self) -> bool:
        """checks if there is only one thing left"""
        return len(self.future) == 0

    def override(self, entry: HistoryEntry) -> None:
        """create a new present item to history and get rid of everything from the saved point onward"""
        self.future = LinkedList([])
        self.past.append(entry)

    def get_history_point(self) -> HistoryEntry:
        """get to the point in history we're at"""
        return self.past[len(self.past) - 1]

    def travel_back(self) -> bool:
        """travel back in history"""
        if len(self.past) >= 2:
            released = self.past.remove_last()
            self.future.insert(0, released)
            return True
        else:
            return False

    def travel_forward(self) -> bool:
        """travel forward in history"""
        if not self.no_future():
            released = self.future.remove_first()
            self.past.append(released)
            return True
        else:
            return False

    def wipe(self) -> None:
        """wipe history"""
        self.past = LinkedList([])
        self.future = LinkedList([])
