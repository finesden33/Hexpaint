"""extra functions to use (instead of importing modules made by others)"""
import math
from typing import Any


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


def hsv_to_rgb(hue: int, saturation: int, velocity: int) -> tuple[int, int, int]:
    """outputs a rgb tuple given a hue, saturation and velocity value
    mathematical procedure is from wikipedia (and then I implemented it into python)"""
    v, s = velocity / 100, saturation / 100
    chroma = v * s
    hue_prime = (hue / 60) % 6
    x = chroma * (1 - abs((hue_prime % 2) - 1))
    r1, g1, b1 = (0, 0, 0)
    if 0 <= hue_prime < 1:
        r1, g1, b1 = (chroma, x, 0)
    elif 1 <= hue_prime < 2:
        r1, g1, b1 = (x, chroma, 0)
    elif 2 <= hue_prime < 3:
        r1, g1, b1 = (0, chroma, x)
    elif 3 <= hue_prime < 4:
        r1, g1, b1 = (0, x, chroma)
    elif 4 <= hue_prime < 5:
        r1, g1, b1 = (x, 0, chroma)
    elif 5 <= hue_prime < 6:
        r1, g1, b1 = (chroma, 0, x)

    m = v - chroma
    return (math.floor((r1 + m) * 255), math.floor((g1 + m) * 255), math.floor((b1 + m) * 255))


def rgb_to_hsv(r: int, g: int, b: int) -> tuple[int, int, int] | tuple[None, int, int]:
    """code curtesy of
    user864331, RGB to HSV Color Conversion Algorithm, URL (version: 2021-05-20): https://math.stackexchange.com/q/3954976
    """
    if r == g == b:
        return 0, 0, math.floor((r / 255) * 100)
    else:
        r /= 255
        g /= 255
        b /= 255
        maxc = max(r, g, b)
        minc = min(r, g, b)
        v = maxc
        if minc == maxc:
            return 0, 0, v
        s = (maxc-minc) / maxc
        rc = (maxc-r) / (maxc-minc)
        gc = (maxc-g) / (maxc-minc)
        bc = (maxc-b) / (maxc-minc)
        if r == maxc:
            h = 0.0+bc-gc
        elif g == maxc:
            h = 2.0+rc-bc
        else:
            h = 4.0+gc-rc
        h = (h/6.0) % 1.0

        return math.floor(h * 360), math.floor(s * 100), math.floor(v * 100)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """converts a rgb tuple to a hex value"""
    r, g, b = rgb
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def colour_add(original_rgb: tuple[int, int, int], new_rgb: tuple[int, int, int], original_alpha: float, new_alpha: float) -> tuple[tuple[int, int, int], float]:
    """adds two colours together, with alpha"""
    a1, a2 = original_alpha, new_alpha
    rgb1, rgb2 = original_rgb, new_rgb

    final_alpha = max(1 - (1 - a1) * (1 - a2), 0.001)

    final_rgb = (min(255, round((rgb1[0] * a1 * (1 - a2) + rgb2[0] * a2) / final_alpha)),
                 min(255, round((rgb1[1] * a1 * (1 - a2) + rgb2[1] * a2) / final_alpha)),
                 min(255, round((rgb1[2] * a1 * (1 - a2) + rgb2[2] * a2) / final_alpha)))
    return (final_rgb, final_alpha)


def long_setattr(address: str, set_val: Any) -> Any:
    """e.g. object.tool.property.value should return the object object.tool.property as the Any and its .value as its str
    address MUST refer to an actual object attribute address"""
    lst = address.split('.')
    setattr(eval('.'.join([str(x) for x in lst[:-1]])), lst[-1], set_val)
