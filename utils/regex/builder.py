from enum import Enum
from .wildcard import get_wildcard_str


class Alignment(Enum):
    LEFT = 1
    RIGHT = 2
    MIDDLE = 3


# wc: wildcard. This means that the pattern_str has to be appended with *, +, {len}, {min,max}
#               before being added to the regex
class Token(Enum):
    DATE_YY = {"pattern_str": r"\d[\d/]{6}\d", "min_len": 8, "max_len": 8, "wildcard": False}
    DATE_YYYY = {"pattern_str": r"\d[\d/]{8}\d", "min_len": 10, "max_len": 10, "wildcard": False}
    NUMBER = {"pattern_str": r"(?:\d[,.\d]*)?\d", "min_len": 1, "max_len": None, "wildcard": False}
    WORD = {"pattern_str": r"\S+", "min_len": 1, "max_len": None, "wildcard": False}
    PHRASE = {"pattern_str": r"\S+(?:\s\S+)*", "min_len": 1, "max_len": None, "wildcard": False}
    WHITESPACE = {"pattern_str": r"\s", "min_len": 1, "max_len": None, "wildcard": True}


class RegexToken:
    default_wildcard_str = "*"

    def __init__(self, token=None, pattern_str=None, min_len=None, max_len=None,
                 capture=False, capture_name=None,
                 value_type=None, value_format=None,
                 wildcard=None,
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
                if token.value['min_len'] is not None:
                    self.min_len = token.value['min_len']
                if token.value['max_len'] is not None:
                    self.max_len = token.value['max_len']
                self.wildcard = token.value['wildcard']

        # If both are defined then pattern_str overrides the pattern_str of token
        if pattern_str is not None:
            self.pattern_str = pattern_str

        if min_len is not None:
            self.min_len = min_len

        if max_len is not None:
            self.max_len = max_len

        self.capture = capture
        self.capture_name = capture_name

        # We force the capture to True if capture_name is set
        if self.capture_name is not None:
            self.capture = True

        self.value_type = value_type
        self.value_format = value_format

        if wildcard is not None:
            self.wildcard = wildcard

        self.multiline = multiline
        if alignment is not None:
            if not isinstance(alignment, Alignment):
                raise RuntimeError("token must be an instance of enum Token")
            else:
                self.alignment = alignment

        self.join_str = join_str

    # TBD: Check how should we handle the case where min_len=0 and max_len=0 as well.
    def regex_str(self):
        token_regex_str = self.pattern_str

        if self.wildcard:
            wildcard_str = get_wildcard_str(self.min_len, self.max_len)
            token_regex_str = "{}{}".format(self.pattern_str, wildcard_str)

        if self.capture:
            if self.capture_name is not None and self.capture_name != "":
                token_regex_str = "(?P<{}>{})".format(self.capture_name, token_regex_str)
            else:
                token_regex_str = "({})".format(token_regex_str)

        return token_regex_str

    def __str__(self):
        return "(r'{}', {}, {})".format(self.pattern_str, self.min_len, self.max_len)


class RegexBuilder:
    def __init__(self):
        self.tokens = []

    def __str__(self):
        for token in self.tokens:
            print(token)

        return "".join(map(lambda tkn: tkn.regex_str(), self.tokens))

    def push_token(self, token):
        self.tokens.append(token)

    def pop_token(self):
        self.tokens.pop()
