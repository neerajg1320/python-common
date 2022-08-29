from dataclasses import dataclass, field
import re
from enum import Enum
from .wildcard import get_wildcard_str
from .patterns import is_regex_comment_pattern, get_regex_comment_pattern, is_whitespace
from utils.regex_utils import regex_apply_on_text, regex_pattern_apply_on_text
import copy


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
                 _min_len=None, _max_len=None, len=None,
                 capture=False, capture_name=None,
                 value_type=None, value_format=None,
                 wildcard=None,
                 multiline=False, alignment=Alignment.LEFT, join_str="\n"):

        if token is None and pattern_str is None:
            raise RuntimeError("Either of the token or string has to be specified")

        self._min_len = -1
        self._max_len = -1

        if token is not None:
            if not isinstance(token, Token):
                raise RuntimeError("token must be an instance of enum Token")
            else:
                self.token = token

                self.pattern_str = token.value['pattern_str']
                if token.value['min_len'] is not None:
                    self._min_len = token.value['min_len']
                if token.value['max_len'] is not None:
                    self._max_len = token.value['max_len']
                self.wildcard = token.value['wildcard']

        # If both are defined then pattern_str overrides the pattern_str of token
        if pattern_str is not None:
            self.pattern_str = pattern_str

        if len is not None:
            self._min_len = len
            self._max_len = len

        if _min_len is not None:
            self._min_len = _min_len

        if _max_len is not None:
            self._max_len = _max_len

        self.capture = capture
        self.capture_name = capture_name

        # We force the capture to True if capture_name is set
        if self.capture_name is not None:
            self.capture = True

        self.value_type = value_type
        self.value_format = value_format

        if wildcard is not None:
            self.wildcard = wildcard

        self._multiline = multiline
        if alignment is not None:
            if not isinstance(alignment, Alignment):
                raise RuntimeError("token must be an instance of enum Token")
            else:
                self.alignment = alignment

        self.join_str = join_str

    def __str__(self):
        return "(r'{}', {}, {}, {})".format(
            self.pattern_str,
            self._min_len,
            self._max_len,
            'M' if self._multiline else 'S'
        )

    @property
    def min_len(self):
        """Minimum Occurrences of the token"""
        return self._min_len

    @min_len.setter
    def set_min_len(self, len):
        self._min_len = len

    @property
    def max_len(self):
        """Maximum Occurrences of the token"""
        return self._max_len

    @max_len.setter
    def set_max_len(self, len):
        self._max_len = len

    @property
    def multiline(self):
        """If Token is Multiline"""
        return self._multiline

    @property
    def token_type(self):
        """Type of RegexToken like DATE, NUMBER etc"""
        return self.token

    # TBD: Check how should we handle the case where min_len=0 and max_len=0 as well.
    def regex_str(self):
        token_regex_str = self.pattern_str

        if self.wildcard:
            wildcard_str = get_wildcard_str(self._min_len, self._max_len)
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
        self.regex_token = token

        if not isinstance(name, str):
            raise RuntimeError("name must be string")
        self.name = name

    def __str__(self):
        return "{}:{}".format(self.name, self.regex_token)

    @property
    def min_len(self):
        """Minimum Occurrences of the token"""
        return self.regex_token.min_len

    @min_len.setter
    def set_min_len(self, len):
        self.regex_token.min_len = len

    @property
    def max_len(self):
        """Maximum Occurrences of the token"""
        return self.regex_token.max_len

    @max_len.setter
    def set_max_len(self, len):
        self.regex_token.max_len = len

    @property
    def multiline(self):
        """If Token is Multiline"""
        return self.regex_token.multiline

    @property
    def token_type(self):
        """Type of RegexToken like DATE, NUMBER etc"""
        return self.regex_token.token

    @property
    def token(self):
        """Contained Regex Token"""
        return self.regex_token

    def regex_str(self):
        return "(?P<{}>{})".format(self.name, self.regex_token.regex_str())


class RegexTokenSet(AbsRegex):
    default_token_join_str = ""

    def __init__(self, flag_full_line=False):
        self.tokens: RegexToken = []
        self.flag_full_line = flag_full_line

    def __str__(self):
        return "\n".join(map(lambda x: str(x), self.tokens))

    def push_token(self, token):
        self.tokens.append(token)

    def pop_token(self):
        self.tokens.pop()

    def set_full_line(self, flag_full_line):
        self.flag_full_line = flag_full_line

    def regex_str(self, newline_between_tokens=False, token_join_str=None):
        join_str = self.default_token_join_str

        if newline_between_tokens:
            join_str = "(?#\n)"

        if token_join_str is not None:
            if not isinstance(token_join_str, str):
                raise RuntimeError("token_join_str must be a string")

            if not is_regex_comment_pattern(token_join_str):
                raise RuntimeError("token_join_str must be a valid Regex Comment Format '{}'".format(
                    get_regex_comment_pattern()
                ))

            join_str = token_join_str

        tokens_regex_str = join_str.join(map(lambda tkn: tkn.regex_str(), self.tokens))

        if self.flag_full_line:
            tokens_regex_str = "^{}$".format(tokens_regex_str)

        return tokens_regex_str

    def token_type_len_str(self, fill_char="X", whitespace_char="S", join_str=" ", alignment=3, debug=False):
        buffer = ""
        for regex_token in self.tokens:
            if regex_token.token_type == Token.WHITESPACE_HORIZONTAL:
                token_char = whitespace_char
            else:
                token_char = fill_char

            format_str = "({{}},{{:>{}}},{{:>{}}})".format(alignment, alignment, alignment)
            token_str = format_str.format(token_char, regex_token.min_len, regex_token.max_len)
            buffer = join_str.join([buffer, token_str])
        return buffer


class FixedRegexTokenSet(RegexTokenSet):
    def __init__(self, *args, **kwargs):
        self._shadow_token_set = None
        super().__init__(*args, **kwargs)

    @property
    def shadow_token_set(self):
        """Shadow Token Set which is used to match following lines"""
        return self._shadow_token_set

    def push_token(self, token):
        if token.min_len != token.max_len:
            raise RuntimeError("min_len must be equal to max_len for FixedRegexTokenSet")

        super().push_token(token)

    def mask_str(self, fill_strategy='all', fill_char="x", whitespace_char=" ", debug=False):
        mask_buffer = ""
        for regex_token in self.tokens:
            if debug:
                print(regex_token.token_type, type(regex_token), regex_token, regex_token.min_len)

            token_mask_len = regex_token.min_len

            token_char = whitespace_char
            if regex_token.token_type != Token.WHITESPACE_HORIZONTAL:
                if fill_strategy == 'all':
                    token_char = fill_char
                elif fill_strategy == 'multi':
                    if regex_token.multiline:
                        token_char = fill_char
                else:
                    raise RuntimeError("Not Supported: fill_strategy {} is not supported".format(fill_strategy))

            token_mask_str = token_char * token_mask_len
            mask_buffer = "".join([mask_buffer, token_mask_str])

        return mask_buffer

    def token_type_len_str(self, fill_char="X", whitespace_char="S", join_str=" ", alignment=3, debug=False):
        buffer = ""
        for regex_token in self.tokens:
            if regex_token.token_type == Token.WHITESPACE_HORIZONTAL:
                token_char = whitespace_char
            else:
                token_char = fill_char

            format_str = "({{}},{{:>{}}})".format(alignment, alignment)
            token_str = format_str.format(token_char, regex_token.min_len)
            buffer = join_str.join([buffer, token_str])
        return buffer

    def generate_shadow_token_set(self):
        self._shadow_token_set = FixedRegexTokenSet(flag_full_line=self.flag_full_line)

        for regex_token in self.tokens:
            if regex_token.token == Token.WHITESPACE_HORIZONTAL or (not regex_token.multiline):
                shd_token = RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=regex_token.min_len, _max_len=regex_token.max_len)
            else:
                shd_token = regex_token

            self._shadow_token_set.push_token(shd_token)

        return self._shadow_token_set


@dataclass
class RegexTextProcessor:
    regex_token_set: RegexTokenSet
    data: str = field(init=False, default=None)
    all_lines_with_offsets: list = field(default_factory=list, init=False)
    matched_lines_data: list = field(default_factory=list, init=False)
    matches_with_absolute_offsets: list = field(default_factory=list, init=False)

    # Our last whitespace token contains the match for \n as well
    def process(self, whitespace_line_tolerance=1, debug=False):
        if self.data is None:
            raise RuntimeError("get_matches_with_token_mask_builder(): data must be set before calling this function")

        # TBD: Can be made as a routine
        # We leave the \n out of the match even though we match the whole line
        result = regex_apply_on_text('^.*$', self.data, flags={"multiline": 1})
        self.all_lines_with_offsets = result["matches"]

        regex_str = self.regex_token_set.regex_str()
        pattern = re.compile(regex_str)
        shadow_pattern = None

        match_count = 0
        whitespace_line_count = 0
        current_matched_line_data = None

        for line_num, line in enumerate(self.all_lines_with_offsets, 1):
            match_text = line['match'][0]
            match_start_offset = line['match'][1]
            match_end_offset = line['match'][2]

            # Line start offset is currently equal to match start offset
            # Line end offset is currently equal to match end offset
            # as we assume that our pattern matches begin at a line start and end at line end
            line_start_offset = match_start_offset

            if is_whitespace(match_text):
                whitespace_line_count += 1
                if whitespace_line_count > whitespace_line_tolerance:
                    # print("whitespace_line_count={}".format(whitespace_line_count))
                    shadow_pattern = None
                continue

            whitespace_line_count = 0

            # We use this to match the line and in case of a match get full and group offsets
            matches_in_line = regex_pattern_apply_on_text(pattern, match_text)

            token_masks = []

            if len(matches_in_line) > 0:
                match_count += 1

                matched_line_data = {
                    'line_num': line_num,
                    'line_match': line['match'],
                    'matches_in_line': matches_in_line,
                    'shadow_lines': []
                }

                # We need this to attach the shadow lines data
                current_matched_line_data = matched_line_data

                if debug or False:
                    print("{:>3}:{}".format(line_num, match_text))

                for match_data in matches_in_line:
                    if debug:
                        print("{:>4}:line_num={}".format(match_count, line_num))
                        print("{}".format(match_text), end="")

                    line_regex_token_set = FixedRegexTokenSet(flag_full_line=self.regex_token_set.flag_full_line)

                    # First token_mask
                    whitespace_token_mask = [r'\s', line_start_offset - match_start_offset, -1]
                    token_masks.append(whitespace_token_mask)
                    for g_idx, group in enumerate(match_data['groups']):
                        if debug:
                            print("  {}: {:>5}:{:>5}: {:>20}:{:>50}".format(g_idx, group[1], group[2], group[3], group[0]))

                        whitespace_token_mask[2] = group[1]
                        line_regex_token_set.push_token(
                            RegexToken(Token.WHITESPACE_HORIZONTAL, len=whitespace_token_mask[2] - whitespace_token_mask[1])
                        )

                        match_token_mask = [r'.', group[1], group[2], group[3]]
                        token_masks.append(match_token_mask)

                        token_name_parts = group[3].split('__')
                        token_multiline = len(token_name_parts) > 1 and token_name_parts[1] == 'M'

                        line_regex_token_set.push_token(
                            NamedToken(
                                RegexToken(Token.ANY_CHAR, len=match_token_mask[2] - match_token_mask[1], multiline=token_multiline),
                                match_token_mask[3]
                            )
                        )

                        whitespace_token_mask = [r'\s', group[2], -1, '']
                        token_masks.append(whitespace_token_mask)

                    # Last token mask
                    whitespace_token_mask[2] = match_end_offset - match_start_offset
                    line_regex_token_set.push_token(
                        RegexToken(Token.WHITESPACE_HORIZONTAL, len=whitespace_token_mask[2] - whitespace_token_mask[1])
                    )

                    # match_data['line_num'] = line_num
                    # match_data['line_match'] = line['match']
                    match_data['fixed_regex_token_set'] = line_regex_token_set

                    # Generate the shadow token set so that we can match the following lines
                    line_regex_token_set.generate_shadow_token_set()
                    if line_regex_token_set.shadow_token_set is not None:
                        shadow_regex_str = line_regex_token_set.shadow_token_set.regex_str()
                        if debug:
                            print("Generated ShadowRegex:{}".format(shadow_regex_str))
                        shadow_pattern = re.compile(shadow_regex_str)

                self.matched_lines_data.append(matched_line_data)

                if debug:
                    print("Token_masks:\n{}".format(token_masks))
                    print("Fixed Regex:\n{}".format(line['mask_regex']))
                    print()
            else:
                if shadow_pattern is not None:
                    shadow_matches_in_line = regex_pattern_apply_on_text(shadow_pattern, match_text)
                    if len(shadow_matches_in_line) > 0:
                        shadow_line_data = {'line_match': line['match'], 'matches_in_line': shadow_matches_in_line}

                        if current_matched_line_data is None:
                            raise RuntimeError("Got shadow_line when current_matched_line_data is None")

                        current_matched_line_data['shadow_lines'].append(shadow_line_data)

                        if debug or False:
                            print("{:>3}:{}".format(line_num, match_text))

    def generate_matches_absolute(self, debug=True):
        if debug:
            print("Generate Matches Absolute")

        for line_data in self.matched_lines_data:
            print(line_data)
            matches_in_line = line_data['matches_in_line']
            shadow_lines = line_data['shadow_lines']

            line_absolute_offset = line_data['line_match'][1]

            # Lines can have multiple matches
            for match_data in matches_in_line:
                # print(line_data)
                self.matches_with_absolute_offsets.append(convert_absolute_offsets(match_data, line_absolute_offset))

            for shadow_line_data in shadow_lines:
                # print("{}".format(shadow_line_data))
                matches_in_line = shadow_line_data["matches_in_line"]
                shadow_line_absolute_offset = shadow_line_data['line_match'][1]
                for match_data in matches_in_line:
                    # print(match_data)
                    self.matches_with_absolute_offsets.append(convert_absolute_offsets(match_data, shadow_line_absolute_offset))


def convert_absolute_offsets(match_data, line_absolute_offset):
    match_linestart_offset = match_data['match'][1]
    match_absolute_offset = line_absolute_offset + match_linestart_offset

    match_absolute_data = copy.deepcopy(match_data["match"])
    groups_absolute_data = copy.deepcopy(match_data["groups"])
    match_absolute_data[1] += match_absolute_offset
    match_absolute_data[2] += match_absolute_offset

    for g_idx, group in enumerate(groups_absolute_data):
        group[1] += match_absolute_offset
        group[2] += match_absolute_offset

    return {'match': match_absolute_data, 'groups': groups_absolute_data}

