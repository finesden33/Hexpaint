"""extra functions to use (instead of importing modules made by others)"""


def cycle_list(lst: list, k: int) -> None:
    """rotates a list by k indexes,
    >>> a = [1,2,3,4]
    >>> cycle_list(a, 2)
    >>> a == [3,4,1,2]
    True
    """
    for _ in range(k):
        last_item = lst[-1]
        for i in range(1, len(lst)):
            lst[-i] = lst[-(i + 1)]
        lst[0] = last_item
