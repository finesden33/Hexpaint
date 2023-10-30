"""Linked list module"""
from __future__ import annotations
from typing import Any, Optional, Iterable
import math


class _Node:
    """A node in a linked list.

    Note that this is considered a "private class", one which is only meant
    to be used in this module by the LinkedList class, but not by client code.

    Instance Attributes:
      - item: The data stored in this node.
      - next: The next node in the list, if any.
    """
    item: Any
    next: Optional[_Node] = None

    def __init__(self, item: Any):
        """initialize a node"""
        self.item = item
        self.next = None


class LinkedList:
    """A linked list implementation of the List ADT.
    """
    # Private Instance Attributes:
    #   - _first: The first node in this linked list, or None if this list is empty.
    _first: Optional[_Node]

    def __init__(self, items: Iterable) -> None:
        """Initialize a new linked list containing the given items.
        """
        self._first = None
        for item in items:
            self.append(item)

    def to_list(self) -> list:
        """Return a built-in Python list containing the items of this linked list.

        The items in this linked list appear in the same order in the returned list.
        """
        items_so_far = []

        curr = self._first
        while curr is not None:
            items_so_far.append(curr.item)
            curr = curr.next

        return items_so_far

    def append(self, item: Any) -> None:
        """Append item to the end of this list.
        """
        new_node = _Node(item)

        if self._first is None:
            self._first = new_node
        else:
            curr = self._first
            while curr.next is not None:
                curr = curr.next
            curr.next = new_node

    def remove_first(self) -> Any:
        """Remove and return the first element of this list.

        Raise an IndexError if this list is empty.
        """
        if self._first is not None:
            pop_val = self._first.item
            self._first = self._first.next
            return pop_val
        else:
            raise IndexError

    def remove_last(self) -> Any:
        """Remove and return the last element of this list.

        Raise an IndexError if this list is empty.
        """
        curr = self._first
        pop_val = 0
        if curr is not None and curr.next is not None:
            while curr.next is not None:
                prev_node, curr = curr, curr.next

                # popping the end (this will be at last while loop iteration)
                if curr.next is None:  # Then if this (next) node is the end node
                    pop_val = curr.item
                    prev_node.next = None  # close off link to the last node on the seocnd last node
            return pop_val

        elif curr is not None:  # if there's only one node, i.e. the first node's next is None (see the if state.)
            pop_val = curr.item
            self._first = None
            return pop_val
        else:
            raise IndexError

    def print_items(self) -> None:
        """Print out each item in this linked list."""
        curr = self._first
        while curr is not None:
            print(curr.item)
            curr = curr.next

    def __getitem__(self, i: int) -> Any:
        """Return the item stored at index i in this linked list.

        Raise an IndexError if index i is out of bounds.

        Preconditions:
            - i >= 0
        """
        curr = self._first
        curr_index = 0
        while curr is not None:
            if curr_index == i:
                return curr.item
            curr = curr.next
            curr_index += 1
        print(curr_index)
        raise IndexError

    def __contains__(self, item: Any) -> bool:
        """Return whether <item> is in this list.

        Use == to compare items.
        """
        curr = self._first
        while curr is not None:
            if curr.item == item:
                return True
            curr = curr.next
        return False

    def __len__(self) -> int:
        """Return the number of elements in this list.
        """
        curr = self._first
        leng = 0
        while curr is not None:
            leng += 1
            curr = curr.next
        return leng

    def __str__(self) -> str:
        """returns string form of the linked list"""
        s = ''
        curr = self._first
        while curr is not None:
            s += f'{str(id(curr))} ,'
            curr = curr.next
        return s

    def count(self, item: Any) -> int:
        """Return the number of times the given item occurs in this list.
        """
        curr = self._first
        occurances = 0
        while curr is not None:
            if curr.item == item:
                occurances += 1
            curr = curr.next
        return occurances

    def index(self, item: Any) -> int:
        """Return the index of the first occurrence of the given item in this list.

        Raise ValueError if the given item is not present.
        """
        curr = self._first
        i = 0
        while curr is not None:
            if curr.item == item:
                return i
            i += 1
            curr = curr.next
        raise ValueError

    def __setitem__(self, i: int, item: Any) -> None:
        """Store item at index i in this list.

        Raise IndexError if i >= len(self).

        Preconditions:
            - i >= 0
        """
        curr = self._first
        c_index = 0
        while curr is not None:
            if c_index == i:
                curr.item = item

            c_index += 1
            curr = curr.next

            if i >= len(self):
                raise IndexError

    def __iter__(self) -> LinkedListIterator:
        """Return an iterator for this linked list.
        """
        return LinkedListIterator(self._first)

    def sum(self) -> int:
        """returns sum of all items in the linked list

        Preconditions:
            - all items in this linked list are ints or floats
        """
        current = self._first
        total = 0
        while current is not None:
            total += current.item
            current = current.next

        return total

    def maximum(self) -> float:
        """Return the maximum element in this linked list.
        Preconditions:
        - every element in this linked list is a float
        - this linked list is not empty
        """
        current = self._first
        maxi = math.inf
        while current is not None:
            maxi = max(current.item, current.next.item)
            current = current.next
        return maxi

    def insert(self, i: int, val: Any) -> None:
        """Insert the given item at index i in this list.
        Raise IndexError if i > len(self).
        Note that adding to the end of the list (i == len(self)) is okay.
        Preconditions:
        - i >= 0
        """
        curr = self._first
        c_index = 0
        new_node = _Node(val)

        if i == 0:
            new_node.next = self._first  # the new node will therefore link to the current first node
            self._first = new_node  # the first node of the list is 'pushed back' to be this new node
            # could've also used a parallel assignment

        else:
            while curr is not None:
                if c_index == i - 1:  # we want to mutate the node at the index before the insert spot
                    new_node.next = curr.next  # make sure our new node links to the node that came after curr node
                    curr.next = new_node  # link the current node (at target index - 1) to our new node
                    return  # acts as return None

                c_index += 1
                curr = curr.next

            raise IndexError

    def pop(self, i: int) -> Any:
        """Remove and return the item at index i.
        Raise IndexError if i >= len(self).
        Preconditions:
        - i >= 0
        """
        curr = self._first
        c_index = 0

        if i >= len(self):  # this covers (curr is None), but it's longer. See tutorial 2 for a faster way
            raise IndexError
        elif i == 0:
            val = curr.item
            self._first = curr.next  # the first node of the list is 'pushed back' to be this new node
            return val
        else:
            while curr is not None:
                if c_index == i - 1:  # note, curr is the node before the node we want to pop
                    if curr.next.next is not None:
                        val = curr.next.item
                        curr.next = curr.next.next  # link the current node (at target index - 1) to our new node
                        return val
                    else:  # i at last node, i.e. curr is 2nd last node
                        val = curr.next.item
                        curr.next = None
                        return val

                c_index += 1
                curr = curr.next

    def remove(self, item: Any) -> None:
        """Remove the first occurence of item from the list.
        Raise ValueError if the item is not found in the list.
        """
        prev, curr = None, self._first
        while not (curr is None or curr.item == item):
            prev, curr = curr, curr.next
        if curr is None:
            raise ValueError
        else:
            if prev is None:
                self._first = curr.next
            else:
                prev.next = curr.next

    def cut(self, i: int) -> None:
        """cuts the linked list to make it shorter. i.e. in list rep: a = [1,2,3,4] then a.cut(2) = a[1,2]
        i.e. it removes every item from i and onward so a.cut(0) = [] for all lists a"""
        curr = self._first
        c_index = 0
        if i > len(self):
            raise IndexError
        while curr is not None:
            if c_index == i - 1:
                curr.next = None
            c_index += 1
            curr = curr.next


class LinkedListIterator:
    """An object responsible for iterating through a linked list.

    This enables linked lists to be used inside for loops!
    """
    # Private Instance Attributes:
    #   - _curr: The current node for this iterator. This should start as the first node
    #            in the linked list, and update to the next node every time __next__
    #            is called.
    _curr: Optional[_Node]

    def __init__(self, first_node: Optional[_Node]) -> None:
        """Initialize a new linked list iterator with the given node."""
        self._curr = first_node

    def __next__(self) -> Any:
        """Return the next item in the iteration.

        Raise StopIteration if there are no more items to return.
        """
        temp_node = self._curr
        if self._curr is not None:
            self._curr = self._curr.next
        else:
            raise StopIteration
        return temp_node.item
