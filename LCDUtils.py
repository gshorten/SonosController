
import math

"""
Module contains common utility functions for working with LCD displays.

"""


def center_text(text):
    """
    Truncates text, centers it, converts to a string.

    :param  text:   text to be centered and truncated
    :type   text:   string
    """

    text_length = len(text)
    if text_length > 16:
        # truncate text if it is too long
        # also convert to a string for good measure, in case we pass an object!
        text = str(text[0:15])
    # calculate how much padding is required to fill display
    padding = math.ceil((16 - text_length) / 2)
    padding_text = " " * (padding)
    # pad the display text to center it.
    display_text = padding_text + text + padding_text
    # make sure it is still 16 characters long; take the first 16 characters
    display_text = display_text[0:15]
    return display_text
