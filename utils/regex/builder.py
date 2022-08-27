import re
from enum import Enum
from .wildcard import get_wildcard_str
from .patterns import is_regex_comment_pattern, get_regex_comment_pattern
from utils.regex_utils import regex_apply_on_text, regex_pattern_apply_on_text


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
    WHITESPACE_ANY = {"pattern_str": r"\s", "min_len": 1, "max_len": None, "wildcard": True}
    WHITESPACE_HORIZONTAL = {"pattern_str": r"[^\S\r\n]", "min_len": 1, "max_len": None, "wildcard": True}
    ANY_CHAR = {"pattern_str": r".", "min_len": 1, "max_len": None, "wildcard": True}


class AbsRegex:
    def regex_str(self):
        raise RuntimeError("Method has to be specified in subclass")


class RegexToken(AbsRegex):
    def __init__(self, token=None, pattern_str=None,
                 min_len=None, max_len=None, len=None,
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

        if len is not None:
            self.min_len = len
            self.max_len = len

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

    def __str__(self):
        return "(r'{}', {}, {})".format(self.pattern_str, self.min_len, self.max_len)

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


class CombineOperator(Enum):
    AND = {"str": ""}
    OR = {"str": "|"}


class CompositeToken(AbsRegex):
    def __init__(self, *args, operator=CombineOperator.OR):
        self.tokens = []

        if not isinstance(operator, CombineOperator):
            raise RuntimeError("operator must be an instance of {}".format(CombineOperator.__name__))

        self.operator = operator

        for arg in args:
            if not isinstance(arg, AbsRegex):
                raise RuntimeError("arg '{}'[{}] is not of type {}".format(arg, type(arg), AbsRegex.__name__))

            self.tokens.append(arg)

    def __str__(self):
        lines = []
        for index, token in enumerate(self.tokens):
            lines.append("token[{}]:{}".format(index, token))
        return "\n".join(lines)

    def regex_str(self):
        regexes = []
        for index, token in enumerate(self.tokens):
            regexes.append(token.regex_str())
        operator_str = self.operator.value["str"]
        return operator_str.join(regexes)


class NamedToken(AbsRegex):
    def __init__(self, token, name):
        if not isinstance(token, AbsRegex):
            raise RuntimeError("token must be an instance of {}".format(AbsRegex.__name__))
        self.token = token

        if not isinstance(name, str):
            raise RuntimeError("name must be string")
        self.name = name

    def __str__(self):
        return "{}:{}".format(self.name, self.token)

    def regex_str(self):
        return "(?P<{}>{})".format(self.name, self.token.regex_str())


class RegexBuilder(AbsRegex):
    default_token_join_str = ""

    def __init__(self, flag_full_line=False):
        self.tokens = []
        self.flag_full_line = flag_full_line

    def __str__(self):
        return "\n".join(map(lambda x: str(x), self.tokens))

    def push_token(self, token):
        self.tokens.append(token)

    def pop_token(self):
        self.tokens.pop()

    def set_full_line(self, flag_full_line):
        self.flag_full_line = flag_full_line

    def regex_str(self, token_lines=False, token_join_str=None):
        join_str = self.default_token_join_str

        if token_lines:
            join_str = "(?#\n)"

        if token_join_str is not None:
            if not isinstance(token_join_str, str):
                raise RuntimeError("token_join_str must be a string")

            if not is_regex_comment_pattern(token_join_str):
                raise RuntimeError("token_join_str must be a valid Regex Comment Format '{}'".format(
                    get_regex_comment_pattern()
                ))

            # print("'{}' valid join str: {}".format(token_join_str, ))

            join_str = token_join_str

        tokens_regex_str = join_str.join(map(lambda tkn: tkn.regex_str(), self.tokens))

        if self.flag_full_line:
            tokens_regex_str = "^{}$".format(tokens_regex_str)

        return tokens_regex_str

    def create(self, token_lines=False):
        return self.regex_str(token_lines=token_lines)

    # Our last whitespace token contains the match for \n as well
    def match_with_token_mask(self, text):
        # TBD: Can be made as a routine
        # We leave the \n out of the match even though we match the whole line
        result = regex_apply_on_text('^.*$', text, flags={"multiline": 1})
        lines_with_offsets = result["matches"]

        regex_str = self.create()
        pattern = re.compile(regex_str)

        extract_matching_lines = False
        match_line_wise = True

        if extract_matching_lines:
            matches = regex_pattern_apply_on_text(pattern, text)
            for m in matches:
                print(m)

        if match_line_wise:
            match_count = 0
            
            for line_num, line in enumerate(lines_with_offsets):
                match_text = line['match'][0]
                match_start_offset = line['match'][1]
                match_end_offset = line['match'][2]

                # Line start offset is currently equal to match start offset
                # Line end offset is currently equal to match end offset
                # as we assume that our pattern matches begin at a line start and end at line end
                line_start_offset = match_start_offset

                match_full_and_groups = regex_pattern_apply_on_text(pattern, match_text)

                token_masks = []

                if len(match_full_and_groups) > 0:
                    match_count += 1

                    first_match = match_full_and_groups[0]
                    print("{:>4}:line_num={}".format(match_count, line_num))
                    print("{}".format(match_text), end="")

                    mask_regex_builder = RegexBuilder(flag_full_line=self.flag_full_line)

                    # First token_mask
                    whitespace_token_mask = [r'\s', line_start_offset - match_start_offset, -1]
                    token_masks.append(whitespace_token_mask)
                    for g_idx, group in enumerate(first_match['groups']):
                        print("  {}: {:>5}:{:>5}: {:>20}:{:>50}".format(g_idx, group[1], group[2], group[3], group[0]))
                        whitespace_token_mask[2] = group[1]
                        mask_regex_builder.push_token(
                            RegexToken(Token.WHITESPACE_HORIZONTAL, len=whitespace_token_mask[2] - whitespace_token_mask[1])
                        )

                        token_mask = [r'.', group[1], group[2], group[3]]
                        token_masks.append(token_mask)
                        mask_regex_builder.push_token(
                            NamedToken(RegexToken(Token.ANY_CHAR, len=token_mask[2] - token_mask[1]), token_mask[3])
                        )

                        whitespace_token_mask = [r'\s', group[2], -1, '']
                        token_masks.append(whitespace_token_mask)

                    # Last token mask
                    whitespace_token_mask[2] = match_end_offset - match_start_offset
                    mask_regex_builder.push_token(
                        RegexToken(Token.WHITESPACE_HORIZONTAL, len=whitespace_token_mask[2] - whitespace_token_mask[1])
                    )

                    print("Token_masks:\n{}".format(token_masks))
                    print("Mask Regex:\n{}".format(mask_regex_builder.create(token_lines=True)))
                    print()

                # Added just for unit testing
                if match_count > 1:
                    break
