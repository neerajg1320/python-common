from dataclasses import dataclass, field
from typing import List
import re
from enum import Enum
from .wildcard import get_wildcard_str
from .patterns import is_regex_comment_pattern, get_regex_comment_pattern, is_whitespace
from utils.regex_utils import regex_apply_on_text, regex_pattern_apply_on_text
from utils.regex.patterns import get_line_matches_from_text
import copy


class Color(Enum):
    COLOR1 = 'rgb(245, 229, 54)'   # yellow-like
    COLOR2 = 'rgb(245, 142, 59)'   # orange-like
    COLOR3 = 'rgb(240, 105, 84)'   # brick-like
    COLOR4 = 'rgb(108, 195, 230)'  # lightblue-like


class Alignment(Enum):
    LEFT = 1
    RIGHT = 2
    MIDDLE = 3


# wc: wildcard. This means that the pattern_str has to be appended with *, +, {len}, {min,max}
#               before being added to the regex
class Token(Enum):
    DATE_YYYY = {"pattern_str": r"\d{2}/\d{2}/\d{4}", "min_len": 10, "max_len": 10, "wildcard": False,
                 "abbr": "DY4", "hash": "D4"}
    DATE_YY = {"pattern_str": r"\d{2}/\d{2}/\d{2}", "min_len": 8, "max_len": 8, "wildcard": False,
               "abbr": "DY2", "hash": "D2"}
    NUMBER = {"pattern_str": r"(?:\d[,.\d]*)?\d", "min_len": 1, "max_len": None, "wildcard": False,
              "abbr": "NUM", "hash": "N"}
    WORD = {"pattern_str": r"\S+", "min_len": 1, "max_len": None, "wildcard": False,
            "abbr": "WRD", "hash": "W"}
    # A phrase currently has a minimum of two words
    PHRASE = {"pattern_str": r"\S+(?:\s\S+)+", "min_len": 1, "max_len": None, "wildcard": False,
              "abbr": "PHR", "hash": "P"}
    WHITESPACE_HORIZONTAL = {"pattern_str": r"[ ]", "min_len": 1, "max_len": None, "wildcard": True,
                             "abbr": "WSH", "hash": "S"}
    # WHITESPACE_HORIZONTAL = {"pattern_str": r"[^\S\r\n]", "min_len": 1, "max_len": None, "wildcard": True,
    #                          "abbr": "WSH", "hash": "S"}
    WHITESPACE_ANY = {"pattern_str": r"\s", "min_len": 1, "max_len": None, "wildcard": True,
                      "abbr": "WSA", "hash": "SA"}
    ANY_CHAR = {"pattern_str": r".", "min_len": 1, "max_len": None, "wildcard": True,
                "abbr": "ANY", "hash": "A"}
    # TBD: The CUSTOM token details shall be defined at the time of the definition
    CUSTOM = {"pattern_str": None, "min_len": None, "max_len": None, "wildcard": False,
              "abbr": None, "hash": None}

    def __str__(self):
        return self.value["abbr"]

    def hash_str(self):
        return self.value["hash"]


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
            self.token if self.token is not None else self.pattern_str,
            self._min_len,
            self._max_len,
            'M' if self._multiline else 'S'
        )

    @property
    def min_len(self):
        """Minimum Occurrences of the token"""
        return self._min_len

    @min_len.setter
    def min_len(self, len):
        self._min_len = len

    @property
    def max_len(self):
        """Maximum Occurrences of the token"""
        return self._max_len

    @max_len.setter
    def max_len(self, len):
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

    def token_str(self):
        if self.token is not None:
            if self.min_len == self.max_len:
                return "{}{{{}}}".format(self.token, self.max_len)
            else:
                return "{}{{{},{}}}".format(self.token, self.min_len, self.max_len)
        else:
            return self.regex_str()

    def token_hash_str(self):
        if self.token is not None:
            return "{}".format(self.token.hash_str())
        else:
            raise RuntimeError("Hash for non-enum tokens has to be supported")

    def is_whitespace(self):
        return self.token == Token.WHITESPACE_HORIZONTAL or self.token == Token.WHITESPACE_ANY

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

    @property
    def multiline(self):
        """If Token is Multiline"""
        return len(self.tokens) > 0 and self.tokens[0].multiline

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

        # name_parts = name.split('__')
        # self.multiline = len(name_parts) > 1 and name_parts[1] == 'M'
        self.name = name

    def __str__(self):
        return "{}:{}".format(self.name, self.regex_token)

    @property
    def min_len(self):
        """Minimum Occurrences of the token"""
        return self.regex_token._min_len

    @min_len.setter
    def min_len(self, len):
        self.regex_token._min_len = len

    @property
    def max_len(self):
        """Maximum Occurrences of the token"""
        return self.regex_token._max_len

    @max_len.setter
    def max_len(self, len):
        self.regex_token._max_len = len

    @property
    def multiline(self):
        """If Token is Multiline"""
        return self.regex_token.multiline

    @multiline.setter
    def multiline(self, flag):
        self.regex_token._multiline = flag

    @property
    def token_type(self):
        """Type of RegexToken like DATE, NUMBER etc"""
        return self.regex_token.token

    @property
    def token(self):
        """Contained Regex Token"""
        return self.regex_token

    @property
    def alignment(self):
        """Alignment of Values in Table"""
        return self.regex_token.alignment

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

    def token_hash_str(self, trim_tail=False, trim_head=False, tail_alignment_tolerance=6, head_alignment_tolerance=4):
        tail_remove_count = 0
        if trim_tail:
            for regex_token in reversed(self.tokens):
                if regex_token.is_whitespace():
                    if regex_token.max_len <= tail_alignment_tolerance:
                        tail_remove_count += 1
                else:
                    break

        head_remove_count = 0
        if trim_head:
            for regex_token in self.tokens:
                if regex_token.is_whitespace():
                    if regex_token.max_len <= head_alignment_tolerance:
                        head_remove_count += 1
                else:
                    break

        size = len(self.tokens)
        tokens_str = "-".join(map(lambda tkn: tkn.token_hash_str(), self.tokens[head_remove_count:size-tail_remove_count]))
        return tokens_str

    def token_str(self):
        tokens_str = "".join(map(lambda tkn: tkn.token_str(), self.tokens))
        return tokens_str

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

    def get_token_by_name(self, token_name):
        for regex_token in self.tokens:
            if isinstance(regex_token, NamedToken) and regex_token.name == token_name:
                return regex_token

    def trim(self, tail_alignment_tolerance=6, head_alignment_tolerance=4):

        tail_remove_count = 0
        for regex_token in reversed(self.tokens):
            if regex_token.is_whitespace():
                if regex_token.max_len <= tail_alignment_tolerance:
                    tail_remove_count += 1
            else:
                break

        head_remove_count = 0
        for regex_token in self.tokens:
            if regex_token.is_whitespace():
                if regex_token.max_len <= head_alignment_tolerance:
                    head_remove_count += 1
            else:
                break

        size = len(self.tokens)
        trimmed_tokens = self.tokens[head_remove_count:size-tail_remove_count]

        trimmed_regex_token_set = RegexTokenSet()
        trimmed_regex_token_set.tokens = trimmed_tokens

        return trimmed_regex_token_set


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

    def adjust_alignment(self, adjustment):
        flag_prev_adjusted = False
        for regex_token in self.tokens:
            if flag_prev_adjusted:
                if regex_token.min_len <= adjustment:
                    raise RuntimeError("Error! adjustment={} is more than regex_token.min_len={}".format(adjustment, regex_token.min_len))
                regex_token.min_len -= adjustment
                regex_token.max_len -= adjustment
                flag_prev_adjusted = False

            if regex_token.multiline:
                if regex_token.alignment == Alignment.LEFT:
                    regex_token.min_len += adjustment
                    regex_token.max_len += adjustment
                    flag_prev_adjusted = True


@dataclass
class RegexTextProcessor:
    regex_token_set: RegexTokenSet
    data: str = field(init=False, default=None)
    status: str = field(init=False, default='NEW')
    all_lines_with_offsets: list = field(default_factory=list, init=False)
    matched_lines_data: list = field(default_factory=list, init=False)
    matches_with_absolute_offsets: list = field(default_factory=list, init=False)
    frame_objects: list = field(default_factory=list, init=False)

    # Our last whitespace token contains the match for \n as well
    def process(self, whitespace_line_tolerance=1, alignment_tolerance=6, debug=False):
        if self.data is None:
            raise RuntimeError("get_matches_with_token_mask_builder(): data must be set before calling this function")

        # TBD: Can be made as a routine
        # We leave the \n out of the match even though we match the whole line
        self.all_lines_with_offsets = get_line_matches_from_text(self.data)

        regex_str = self.regex_token_set.regex_str()
        pattern = re.compile(regex_str)
        shadow_pattern = None
        shadow_token_set = None

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

                        main_regex_token = self.regex_token_set.get_token_by_name(group[3])
                        # print("main_regex_token={}".format(main_regex_token))

                        line_regex_token_set.push_token(
                            NamedToken(
                                RegexToken(Token.ANY_CHAR,
                                           len=match_token_mask[2] - match_token_mask[1],
                                           multiline=main_regex_token.multiline),
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

                    match_data['fixed_regex_token_set'] = line_regex_token_set

                    # Generate the shadow token set so that we can match the following lines
                    line_regex_token_set.generate_shadow_token_set()
                    if line_regex_token_set.shadow_token_set is not None:
                        shadow_regex_str = line_regex_token_set.shadow_token_set.regex_str()
                        if debug:
                            print("Generated ShadowRegex:{}".format(shadow_regex_str))
                        shadow_pattern = re.compile(shadow_regex_str)
                        shadow_token_set = line_regex_token_set.shadow_token_set

                self.matched_lines_data.append(matched_line_data)

                if debug:
                    print("Token_masks:\n{}".format(token_masks))
                    print("Fixed Regex:\n{}".format(line['mask_regex']))
                    print()
            else:
                if shadow_pattern is not None:
                    adjustment = 0
                    shadow_matches_in_line = regex_pattern_apply_on_text(shadow_pattern, match_text)

                    if len(shadow_matches_in_line) < 1:
                        if alignment_tolerance > 0 and True:

                            for adjustment in range(1, alignment_tolerance+1):
                                # print("Shadow  :{}".format(shadow_token_set.regex_str()))
                                try:
                                    shadow_token_set.adjust_alignment(1)
                                    # print("Adjusted:{}".format(shadow_token_set.regex_str()))
                                    adjusted_shadow_pattern = re.compile(shadow_token_set.regex_str())
                                    shadow_matches_in_line = regex_pattern_apply_on_text(adjusted_shadow_pattern, match_text)
                                    if len(shadow_matches_in_line) > 0:
                                        # print("Adjustment={} Found Match: {}".format(adjustment, match_text))
                                        break
                                except RuntimeError as e:
                                    print(e)
                                    break
                                    
                            shadow_token_set.adjust_alignment(-adjustment)

                    if len(shadow_matches_in_line) > 0:
                        shadow_line_data = {
                            'adjustment': adjustment,
                            'line_match': line['match'],
                            'matches_in_line': shadow_matches_in_line
                        }

                        if current_matched_line_data is None:
                            raise RuntimeError("Got shadow_line when current_matched_line_data is None")

                        current_matched_line_data['shadow_lines'].append(shadow_line_data)

                        if debug or False:
                            print("{:>3}:{}".format(line_num, match_text))

    # We are currently generating separate match item for match line and shadow match line
    def generate_matches_absolute(self, debug=False):
        if debug:
            print("Generate Matches Absolute")

        for line_data in self.matched_lines_data:
            matches_in_line = line_data['matches_in_line']
            shadow_lines = line_data['shadow_lines']

            line_absolute_offset = line_data['line_match'][1]
            # Lines can have multiple matches
            for match_data in matches_in_line:
                # print(line_data)
                self.matches_with_absolute_offsets.append(self.convert_absolute_offsets(match_data, line_absolute_offset))

            # There can be multiple shadow lines
            for shadow_line_data in shadow_lines:
                # print("{}".format(shadow_line_data))
                matches_in_line = shadow_line_data["matches_in_line"]
                shadow_line_absolute_offset = shadow_line_data['line_match'][1]
                for match_data in matches_in_line:
                    # print(match_data)
                    self.matches_with_absolute_offsets.append(self.convert_absolute_offsets(match_data, shadow_line_absolute_offset))

    def generate_frame_objects(self, shadow_join_str="", shadow_trim=False, debug=False):
        if debug:
            print("Generate Frame")

        for line_data in self.matched_lines_data:
            matches_in_line = line_data['matches_in_line']
            shadow_lines = line_data['shadow_lines']

            # Lines can have multiple matches
            for match_data in matches_in_line:
                match_object = {}
                for group in match_data['groups']:
                    match_object[group[3]] = group[0]
                self.frame_objects.append(match_object)

            # There can be multiple shadow lines
            for shadow_line_data in shadow_lines:
                matches_in_line = shadow_line_data["matches_in_line"]
                for match_data in matches_in_line:
                    for group in match_data['groups']:
                        # print("Need to add '{}' in '{}'".format(group[0], group[3]))
                        shadow_group_str = group[0]
                        # print("shadow_trim:{}".format(shadow_trim))
                        if shadow_trim:
                            shadow_group_str = shadow_group_str.strip()
                            # print("shadow_group_str={}".format(shadow_group_str))
                        match_object[group[3]] = shadow_join_str.join([match_object[group[3]], shadow_group_str])

    @staticmethod
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


@dataclass
class RegexDictionary:
    tokens: List[RegexToken] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.tokens.append(RegexToken(Token.DATE_YYYY))
        self.tokens.append(RegexToken(Token.DATE_YY))
        # Disabled for unit testing
        # self.tokens.append(RegexToken(Token.NUMBER))
        # Phrases are detected by combining words
        # self.tokens.append(RegexToken(Token.PHRASE))
        self.tokens.append(RegexToken(Token.WORD))
        self.tokens.append(RegexToken(Token.WHITESPACE_HORIZONTAL))

    def __str__(self):
        return "\n".join(map(lambda x: "{}:{}".format(type(x).__name__, str(x)), self.tokens))

    def token_first(self, text, debug=False):
        match_count = 0
        for token in self.tokens:
            token_regex_str = "^{}".format(token.regex_str())
            if debug:
                print("token_regex_str='{}' text='{}'".format(token_regex_str, text))
            token_pattern = re.compile(token_regex_str)

            matches = regex_pattern_apply_on_text(token_pattern, text)
            match_count = len(matches)
            if len(matches) > 0:
                break

        if match_count != 1:
            raise RuntimeError("Error! found {} tokens. need to fix token detection logic to find exactly one".format(len(matches)))

        token_match = matches[0]['match']

        if debug:
            print("token={} token_match={}".format(token, token_match))

        return token, token_match


@dataclass
class RegexGenerator:
    regex_dictionary: RegexDictionary
    regex_colors: [] = field(init=False, default_factory=list)
    phrase_space_tolerance: int = 1

    def __post_init__(self):
        self.regex_colors.append(Color.COLOR1)
        self.regex_colors.append(Color.COLOR2)
        self.regex_colors.append(Color.COLOR3)
        self.regex_colors.append(Color.COLOR4)

    def __str__(self):
        return "Regex Dictionary: {}".format(self.regex_dictionary)

    @staticmethod
    def create_phrase_token(phrase_tokens, debug=False):
        token_len = 0

        for item in phrase_tokens:
            if debug:
                print("token={}".format(item['token']))
            token_len += item['token'].max_len

        return RegexToken(Token.PHRASE, len=token_len)

    @staticmethod
    def add_to_phrase_tokens(token_list, token, value, offset):
        token_list.append({'token': token, 'value': value, 'offset': offset})

    def generate_tokens(self, text, detect_phrases=True, debug=False):
        start_offset = 0
        text_len = len(text)

        if detect_phrases:
            phrase_start_offset = -1
            phrase_lookup_started = False
            phrase_lookup_ended = False
            phrase_tokens = []
            phrase_word_count = 0

        while start_offset < text_len:
            rem_text = text[start_offset:]

            regex_token, token_match = self.regex_dictionary.token_first(rem_text)
            # Set the offset from the start of the text
            token_match[1] += start_offset
            token_match[2] += start_offset

            token_match_len = token_match[2] - token_match[1]

            match_token = copy.deepcopy(regex_token)
            match_token.min_len = token_match_len
            match_token.max_len = token_match_len

            next_lookup_offset = start_offset + token_match_len

            if not detect_phrases:
                if debug:
                    print("match_token={} token_match='{}'".format(match_token, token_match))
                yield match_token, token_match
            else:
                if next_lookup_offset >= text_len:
                    if phrase_lookup_started:
                        phrase_lookup_ended = True
                else:
                    if regex_token.token == Token.WORD:
                        self.add_to_phrase_tokens(phrase_tokens, match_token, token_match, start_offset)
                        # phrase_tokens.append(match_token)
                        if debug:
                            print("Added token '{}' to phrase".format(match_token))
                        if not phrase_lookup_started:
                            phrase_lookup_started = True
                            phrase_start_offset = start_offset
                        # Increment the phrase word count
                        phrase_word_count += 1
                    elif regex_token.token == Token.WHITESPACE_HORIZONTAL:
                        if phrase_lookup_started:
                            if token_match_len <= self.phrase_space_tolerance:
                                self.add_to_phrase_tokens(phrase_tokens, match_token, token_match, start_offset)
                                # phrase_tokens.append(match_token)
                                if debug:
                                    print("Added token '{}' to phrase".format(match_token))
                            else:
                                phrase_lookup_ended = True
                    else:
                        if phrase_lookup_started:
                            phrase_lookup_ended = True

                if phrase_lookup_ended:
                    if phrase_word_count > 1:
                        # If last item in the phrase_tokens is a space then that space is not part of phrase
                        last_space_item = None
                        if phrase_tokens[-1]['token'].token == Token.WHITESPACE_HORIZONTAL:
                            last_space_item = phrase_tokens[-1]
                            phrase_tokens = phrase_tokens[:-1]

                        phrase_token = self.create_phrase_token(phrase_tokens)
                        phrase_token_match = [text[phrase_start_offset : phrase_start_offset + phrase_token.max_len],
                                              phrase_start_offset,
                                              phrase_start_offset + phrase_token.max_len]
                        if debug:
                            print("phrase_token={} token_match='{}'".format(phrase_token, phrase_token_match))
                        yield phrase_token, phrase_token_match

                        if last_space_item is not None:
                            if debug:
                                print("last_space_token={} token_match='{}'".format(last_space_item['token'], last_space_item['value']))
                            yield last_space_item['token'], last_space_item['value']
                    else:
                        for item in phrase_tokens:
                            if debug:
                                print("match_token={} token_match='{}'".format(item['token'], item['value']))
                            yield item['token'], item['value']

                    phrase_lookup_started = False
                    phrase_lookup_ended = False
                    phrase_word_count = 0
                    phrase_tokens.clear()

                if not phrase_lookup_started:
                    if debug:
                        print("match_token={} token_match='{}'".format(match_token, token_match))
                    yield match_token, token_match
            # detect phrases

            start_offset = next_lookup_offset

        if detect_phrases and phrase_lookup_started:
            print("A phrase is pending")

    def generate_token_sequence_and_verify_regex(self, line_text, debug=False):
        # Used for unit testing, to be placed in generate_tokens call
        # line_text_skewed = line_text[:-2]

        regex_line_token_seq = RegexTokenSet(flag_full_line=True)

        if debug:
            print("Generate Tokens:")
        for token, value in self.generate_tokens(line_text):
            if debug:
                print("Token Match:{} Value={}".format(token, value))
            regex_line_token_seq.push_token(token)

        # Create regex from generated tokens
        line_regex_str = regex_line_token_seq.regex_str()
        if debug:
            print("Regex Str:{}".format(regex_line_token_seq.regex_str()))
            print("Tokens Str:{}".format(regex_line_token_seq.token_str()))

        matches = regex_apply_on_text(line_regex_str, line_text)['matches']
        if len(matches) > 0:
            if debug:
                print("The regex generation is successful")
                print(matches)
        else:
            raise RuntimeError("The generated regex '{}' did not produce match with input text '{}'".
                               format(line_regex_str, line_text))

        return regex_line_token_seq

    def generate_regex_token_sequence_per_line_from_text(self, text):
        sample_offset = 0
        sample_size = 1000000
        lines_with_offsets = get_line_matches_from_text(text)[sample_offset:sample_offset+sample_size]
        for line_num, line_data in enumerate(lines_with_offsets, 1):
            line_text = line_data['match'][0]
            line_token_seq = self.generate_token_sequence_and_verify_regex(line_text)
            yield {"num": line_num, "text": line_text, 'token_sequence': line_token_seq}

    def generate_regex_token_hashes_from_text(self, text):
        for line_item in self.generate_regex_token_sequence_per_line_from_text(text):
            line_item.update({'token_hash': line_item['token_sequence'].token_hash_str()})
            yield line_item

    def get_token_hash_map(self, text):
        token_hash_map = {}
        for line_item in self.generate_regex_token_hashes_from_text(text):
            key = line_item['token_hash']
            if key not in token_hash_map:
                group_token_sequence = copy.deepcopy(line_item['token_sequence'])
                print("LineNum:{} group_token_sequence='{}'".format(line_item['num'], group_token_sequence.token_str()))
                # TBD: This happens in case line has no char. Need to check if we should assign a token
                if group_token_sequence.token_str() == '':
                    print(group_token_sequence)
                token_hash_map[key] = {'group_token_sequence': group_token_sequence, 'line_items': []}

            group_token_sequence = token_hash_map[key]['group_token_sequence']
            item_token_sequence = line_item['token_sequence']

            try:
                for token_index in range(len(group_token_sequence.tokens)):
                    if group_token_sequence.tokens[token_index].min_len > item_token_sequence.tokens[token_index].min_len:
                        group_token_sequence.tokens[token_index].min_len = item_token_sequence.tokens[token_index].min_len
                    if group_token_sequence.tokens[token_index].max_len < item_token_sequence.tokens[token_index].max_len:
                        group_token_sequence.tokens[token_index].max_len = item_token_sequence.tokens[token_index].max_len
            except IndexError as e:
                print("IndexError:")
                print("group_token_sequence:{}".format(group_token_sequence.token_str()))
                print(" item_token_sequence:{}".format(item_token_sequence.token_str()))

            token_hash_map[key]['line_items'].append(line_item)
        return token_hash_map


def build_and_apply_regex(text, flags=None):
    regex_dictionary = RegexDictionary()
    regex_generator = RegexGenerator(regex_dictionary)

    print("Regex Token Sequences:")
    for line_item in regex_generator.generate_regex_token_sequence_per_line_from_text(text):
        print("{}:{}".format(line_item['num'], line_item['token_sequence'].token_str()))

    print("Regex Token Hashes:")
    for line_item in regex_generator.generate_regex_token_hashes_from_text(text):
        print("{}:{}".format(line_item['num'], line_item['token_hash']))

    print("Regex Token Hashmap:")
    token_hash_map = regex_generator.get_token_hash_map(text)
    result = None
    color_index = 0
    for token_hash_key, token_hash_matches in token_hash_map.items():
        item_count = len(token_hash_matches['line_items'])
        group_regex_str = token_hash_matches['group_token_sequence'].regex_str()

        token_hash_regex_match_result = regex_apply_on_text(group_regex_str, text, flags={"multiline": 1})
        regex_match_count = len(token_hash_regex_match_result['matches'])

        token_hash_key_token_count = len(token_hash_matches['group_token_sequence'].tokens)
        token_hash_key_sample_count = len(token_hash_matches['line_items'])

        # Sampled for debugging. token_hash_key_count to be removed when sampling finished.
        # if item_count != regex_match_count and token_hash_key == "S-D2-S-P-S-W-S-D2-S-N-S-N":
        # if True:
        if "D2" in token_hash_key:
            print("{:<30}[{:>3}]".format(token_hash_key, token_hash_key_sample_count))
            # print("    group_token_sequence:{}".format(token_hash_matches['group_token_sequence'].token_str()))
            # print("    group_regex_str={}".format(group_regex_str))
            # print("Sample Count={:>4}".format(token_hash_key_sample_count))
            # print(" Match Count={:>4}".format(len(token_hash_regex_match_result['matches'])))

            for matches in token_hash_regex_match_result['matches']:
                matches['match'].append(regex_generator.regex_colors[color_index].value)

            color_index = (color_index + 1) % len(regex_generator.regex_colors)

            if result is None:
                result = token_hash_regex_match_result
            else:
                result['matches'].extend(token_hash_regex_match_result['matches'])

    return result
