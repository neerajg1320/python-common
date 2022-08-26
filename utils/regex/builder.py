from enum import Enum


class Alignment(Enum):
    LEFT = 1
    RIGHT = 2
    MIDDLE = 3


class Token(Enum):
    DATE_YY = {"pattern_str": r"\d[\d/]{6}\d", "min_len": 8, "max_len": 8}
    DATE_YYYY = {"pattern_str": r"\d[\d/]{8}\d", "min_len": 10, "max_len": 10}
    NUMBER = {"pattern_str": r"(?:\d[,.\d]*)?\d", "min_len": 1, "max_len": None}
    WORD = {"pattern_str": r"\S+", "min_len": 1, "max_len": None}
    PHRASE = {"pattern_str": r"\S+(?:\s\S+)*", "min_len": 1, "max_len": None}


class RegexToken:

    def __init__(self, token=None, pattern_str=None, min_len=None, max_len=None,
                 value_type=None, value_format=None,
                 multiline=False, alignment=Alignment.LEFT, join_str="\n"):

        if token is None and pattern_str is None:
            raise RuntimeError("Either of the token or string has to be specified")

        self.min_len = -1
        self.max_len = -1

        if token is not None:
            if not isinstance(token, Token):
                raise RuntimeError("token must be an instance of enum Token")
            else:
                self.pattern_str = token.value['pattern_str']
                self.min_len = token.value['min_len']
                self.max_len = token.value['max_len']

        # If both are defined then pattern_str overrides the pattern_str of token
        if pattern_str is not None:
            self.pattern_str = pattern_str

        if min_len is not None:
            self.min_len = min_len

        if max_len is not None:
            self.max_len = max_len

        self.value_type = value_type
        self.value_format = value_format

        self.multiline = multiline
        if alignment is not None:
            if not isinstance(alignment, Alignment):
                raise RuntimeError("token must be an instance of enum Token")
            else:
                self.alignment = alignment

        self.join_str = join_str

    def __str__(self):
        return "(r'{}', {}, {})".format(self.pattern_str, self.min_len, self.max_len)
