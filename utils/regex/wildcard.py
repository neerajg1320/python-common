def get_wildcard_str(min_len, max_len):
    if max_len < 0:
        # If min_len = -1 i.e. not specified then we treat it as 0
        if min_len <= 0:
            wildcard_str = "*"
        elif min_len == 1:
            wildcard_str = "+"
        else:
            wildcard_str = "{{{},}}".format(min_len)
    elif max_len == 1:
        # If min_len = -1 i.e. not specified then we treat it as 0
        if min_len <= 0:
            wildcard_str = "?"
        elif min_len == 1:
            wildcard_str = ""
        else:
            raise RuntimeError("min_len={} cannot be greater than max_len={}".format(min_len, max_len))
    # Case max_len > 1, signifies no wildcard possible
    else:
        if min_len < 0:
            wildcard_str = "{{,{}}}".format(max_len)
        else:
            if min_len > max_len:
                raise RuntimeError("min_len={} cannot be greater than max_len={}".format(min_len, max_len))
            elif min_len == max_len:
                wildcard_str = "{{{}}}".format(min_len)
            else:
                wildcard_str = "{{{},{}}}".format(min_len, max_len)

    return wildcard_str
