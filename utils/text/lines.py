from collections import OrderedDict


def get_text_shape(text):
    text_shape = {"lines": OrderedDict()}
    lines = text.splitlines()
    for index, line in enumerate(lines):
        text_shape["lines"][index] = len(line)

    text_shape["count"] = len(lines)

    return text_shape


# Given a string buffer return the max line length
def get_max_line_length(text):
    max_len = 0
    if text is not None:
        for line in text.splitlines():
            line_len = len(line)
            if line_len > max_len:
                max_len = line_len

    return max_len


def pad_lines(text, length, padding_char=' ', join_char="\n"):
    buffer = ""
    for line in text.splitlines():
        padded_line = line.ljust(length, padding_char)
        buffer = join_char.join([buffer, padded_line])

    return buffer
