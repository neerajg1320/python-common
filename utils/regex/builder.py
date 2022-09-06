from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re
from enum import Enum
from .wildcard import get_wildcard_str
from .patterns import is_regex_comment_pattern, get_regex_comment_pattern, is_whitespace
from utils.regex.apply import regex_apply_on_text, regex_pattern_apply_on_text
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
    PHRASE_OR_WORD = {"pattern_str": r"\S+(?:\s\S+)*", "min_len": 1, "max_len": None, "wildcard": False,
                      "abbr": "PHW", "hash": "P"}
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


class CombineOperator(Enum):
    AND = {"str": ""}
    OR = {"str": "|"}


class AbsRegex:
    def regex_str(self):
        raise RuntimeError("Method has to be specified in subclass")


@dataclass
class RegexToken(AbsRegex):
    components: List = field(init=False)
    operator: CombineOperator = field(init=False)
    token: Token = field(init=False)
    pattern_str: str = field(init=False)
    min_len: int = field(init=False)
    max_len: int = field(init=False)
    capture: bool = field(init=False)
    capture_name: str = field(init=False)
    wildcard: bool = field(init=False)
    multiline: bool = field(init=False)
    alignment: Alignment = field(init=False)
    join_str: str = field(init=False)

    def __init__(self, token=None, components=None, operator=None,
                 pattern_str=None,
                 min_len=None, max_len=None, len=None,
                 capture=False, capture_name=None,
                 wildcard=None,
                 multiline=False, alignment=Alignment.LEFT, join_str="\n"):

        self.components = components
        if components is not None:
            if token is not None:
                raise RuntimeError("Only one of the token or tokens can be present")
            if operator is None:
                raise RuntimeError("An operator must be present when components are specified")

            for component in components:
                if not isinstance(component, RegexToken):
                    raise RuntimeError("component has to be of type {}".format(self.__class__.__name__))

            self.components = components
            self.operator = operator
            join_str = operator.value['str']
            self.pattern_str = join_str.join(map(lambda c: c.regex_str(), components))
            self.wildcard = False
        else:
            if token is None and pattern_str is None:
                raise RuntimeError("Either of the token, tokens or pattern_str has to be specified")

        self.min_len = -1
        self.max_len = -1

        self.token = token
        if token is not None:
            if isinstance(token, Token):
                self.pattern_str = token.value['pattern_str']
                if token.value['min_len'] is not None:
                    self.min_len = token.value['min_len']
                if token.value['max_len'] is not None:
                    self.max_len = token.value['max_len']
                self.wildcard = token.value['wildcard']
            elif isinstance(token, RegexToken):
                self.pattern_str = token.regex_str()
                self.min_len = token.min_len
                self.max_len = token.max_len
                self.wildcard = token.wildcard
            else:
                raise RuntimeError("token [{}] must be an instance of enum Token or RegexToken".format(type(token)))

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
        if self.components is not None:
            return " | ".join(map(lambda c: "{}:{}".format("c", str(c)), self.components))
            # return "[components]"

        return "({}, r'{}', {}, {}, {})".format(
            type(self).__name__,
            self.token if self.token is not None else self.pattern_str,
            # self.pattern_str,
            # "token",
            self.min_len,
            self.max_len,
            'M' if self.multiline else 'S'
        )

    # Kept for reference:
    #
    # @property
    # def min_len(self):
    #     """Minimum Occurrences of the token"""
    #     return self._min_len
    #
    # @min_len.setter
    # def min_len(self, len):
    #     self._min_len = len

    def set_token(self, token):
        self.token = token
        self.pattern_str = token.value['pattern_str']

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


@dataclass
class RegexTokenSequence(AbsRegex):
    default_token_join_str: str = ""
    tokens: List = field(default_factory=list)
    flag_full_line: bool = field(default=False)

    def __str__(self):
        return "\n".join(map(lambda x: str(x), self.tokens))

    def push_token(self, token):
        self.tokens.append(token)

    def pop_token(self):
        self.tokens.pop()

    def set_full_line(self, flag_full_line):
        self.flag_full_line = flag_full_line

    def generate_named_token_sequence(self, non_space_tokens=True, space_tokens=False):
        self.named_token_sequence = RegexTokenSequence(flag_full_line=self.flag_full_line)

        for tkn_idx, regex_token in enumerate(self.tokens):
            if regex_token.is_whitespace():
                if space_tokens:
                    regex_token.capture_name = "Token{}".format(tkn_idx)
            else:
                if non_space_tokens:
                    regex_token.capture_name = "Token{}".format(tkn_idx)

            self.named_token_sequence.push_token(regex_token)

        return self.named_token_sequence

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

    def token_hash_str(self):
        tokens_str = "-".join(map(lambda tkn: tkn.token_hash_str(), self.tokens))
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
            if isinstance(regex_token, RegexToken) and regex_token.capture_name == token_name:
                return regex_token

    def trim(self, trim_head=True, trim_tail=True, tail_alignment_tolerance=6, head_alignment_tolerance=4):
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
        trimmed_tokens = self.tokens[head_remove_count:size-tail_remove_count]

        trimmed_regex_token_sequence = RegexTokenSequence()
        trimmed_regex_token_sequence.tokens = trimmed_tokens

        return trimmed_regex_token_sequence

    def is_similar(self, second_token_sequence, trim=True, debug=False):
        if debug or False:
            print("  Self Tokens:\n{}".format(self.token_str()))
            print("Second Tokens:\n{}".format(second_token_sequence.token_str()))

        if trim:
            self_trim = self.trim()
            second_token_sequence_trim = second_token_sequence.trim()
        else:
            self_trim = self
            second_token_sequence_trim = second_token_sequence

        flag_match = True
        for idx, regex_token in enumerate(self_trim.tokens):
            if idx >= len(second_token_sequence_trim.tokens):
                flag_match = False
                break

            second_regex_token = second_token_sequence_trim.tokens[idx]
            if regex_token.token != second_regex_token.token:
                if debug:
                    print("Token mismatch {} and {}".format(regex_token.token, second_regex_token.token))

                flag_match = False
                if regex_token.token == Token.WORD:
                    if second_regex_token.token == Token.PHRASE:
                        regex_token.set_token(Token.PHRASE_OR_WORD)
                        flag_match = True
                elif regex_token.token == Token.PHRASE:
                    if second_regex_token.token == Token.WORD:
                        regex_token.set_token(Token.PHRASE_OR_WORD)
                        flag_match = True
                elif regex_token.token == Token.PHRASE_OR_WORD:
                    if second_regex_token.token == Token.PHRASE:
                        flag_match = True
                    elif second_regex_token.token == Token.WORD:
                        flag_match = True

                if not flag_match:
                    break

        # If match is there then either of following could be true
        # trivial prefix match: group_token_sequence is []
        # prefix match: len(second_token_sequence) > len(self.token_sequence)
        # complete match:
        if flag_match:
            if len(second_token_sequence_trim.tokens) > len(self_trim.tokens):
                if debug:
                    print("Prefix Match: Ignored")
                flag_match = False
            elif len(second_token_sequence_trim.tokens) == len(self_trim.tokens):
                if len(self_trim.tokens) == 0:
                    if debug:
                        print("Blank Match")
                else:
                    if len(self.tokens) != len(second_token_sequence.tokens):
                        if debug:
                            print("Complete Trim Match")

                        # TBD: This needs to be corrected. We need to address head_trim as well
                        if len(second_token_sequence.tokens) > len(self.tokens):
                            last_token_of_second = second_token_sequence.tokens[-1]
                            if last_token_of_second.token != Token.WHITESPACE_HORIZONTAL:
                                print("second_token_sequence {} head_trim correction not supported yet".format(
                                    second_token_sequence.token_str())
                                )
                                flag_match = False
                            else:
                                self.tokens.append(RegexToken(Token.WHITESPACE_HORIZONTAL,
                                                              min_len=0,
                                                              max_len=last_token_of_second.max_len))
                        else:
                            last_token_of_self = self.tokens[-1]
                            if last_token_of_self.token != Token.WHITESPACE_HORIZONTAL:
                                print("self {} head_trim correction not supported yet".format(self.token_str()))
                                flag_match = False
                            else:
                                last_token_of_self.min_len = 0
                    else:
                        if debug:
                            print("Complete Match")
            else:
                # In this case flag_match should be set to false in the above block
                raise RuntimeError("This should not have happened. Examine logic")

        return flag_match

    def apply(self, text):
        regex_text_processor = RegexTextProcessor(self)
        regex_text_processor.data = text

        regex_text_processor.process(whitespace_line_tolerance=1, alignment_tolerance=6)

        sample_offset = 0
        sample_size = 10
        matched_lines_sample = regex_text_processor.matched_lines_data[sample_offset:sample_size]

        print("Show Matched Lines Sample size={}".format(sample_size))
        for index, line_data in enumerate(matched_lines_sample):
            print("[{:>4}]  LineNum:{}".format(index, line_data['line_num']))

            for l_match_data in line_data['matches_in_line']:
                print("    Match: {}".format(l_match_data['match']))
                print("    Groups: {}".format(l_match_data['groups']))
                # print("    FixedRegexTokenSequence: {}".format(l_match['fixed_regex_token_sequence']))
                print("    FixedRegex:{}".format(l_match_data['fixed_regex_token_sequence'].regex_str()))
                print("    ShadowRegex:{}".format(l_match_data['fixed_regex_token_sequence'].shadow_token_sequence.regex_str()))

        alignment_analysis = False
        if alignment_analysis:
            print("The Mask Map:")
            for index, line_data in enumerate(matched_lines_sample):
                for l_match_data in line_data['matches_in_line']:
                    print("{:>4}: {}".format(index, l_match_data['fixed_regex_token_sequence'].mask_str()))
                    print("{:>4}: {}".format(index, l_match_data['fixed_regex_token_sequence'].shadow_token_sequence.mask_str()))

            print("The Text Lines:")
            for index, line_data in enumerate(matched_lines_sample):
                for l_match_data in line_data['matches_in_line']:
                    print("{:>4}: {}".format(index, l_match_data['match'][0]))

            print("The Token Lengths Map:")
            for index, line_data in enumerate(matched_lines_sample):
                for l_match_data in line_data['matches_in_line']:
                    print("{}".format(l_match_data['fixed_regex_token_sequence'].token_type_len_str()))
            # The next stage we will fix the alignment for the columns

        return regex_text_processor


@dataclass
class FixedRegexTokenSequence(RegexTokenSequence):
    shadow_token_sequence: RegexTokenSequence = field(init=False)

    def push_token(self, token):
        if token.min_len != token.max_len:
            raise RuntimeError("min_len must be equal to max_len for FixedRegexTokenSequence")

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

    def generate_shadow_token_sequence(self):
        self.shadow_token_sequence = FixedRegexTokenSequence(flag_full_line=self.flag_full_line)

        for regex_token in self.tokens:
            if regex_token.token == Token.WHITESPACE_HORIZONTAL or (not regex_token.multiline):
                shd_token = RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=regex_token.min_len, max_len=regex_token.max_len)
            else:
                shd_token = regex_token

            self.shadow_token_sequence.push_token(shd_token)

        return self.shadow_token_sequence

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
    regex_token_sequence: RegexTokenSequence
    data: str = field(init=False, default=None)
    status: str = field(init=False, default='NEW')
    all_lines_with_offsets: list = field(default_factory=list, init=False)
    matched_lines_data: list = field(default_factory=list, init=False)
    matches_with_absolute_offsets: list = field(default_factory=list, init=False)
    frame_objects: list = field(default_factory=list, init=False)

    # Our last whitespace token contains the match for \n as well
    def process(self, whitespace_line_tolerance=0, alignment_tolerance=0, debug=False):
        if self.data is None:
            raise RuntimeError("get_matches_with_token_mask_builder(): data must be set before calling this function")

        # TBD: Can be made as a routine
        # We leave the \n out of the match even though we match the whole line
        self.all_lines_with_offsets = get_line_matches_from_text(self.data)

        regex_str = self.regex_token_sequence.regex_str()
        pattern = re.compile(regex_str)
        shadow_pattern = None
        shadow_token_sequence = None

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

                    line_regex_token_sequence = FixedRegexTokenSequence(flag_full_line=self.regex_token_sequence.flag_full_line)

                    # First token_mask
                    whitespace_token_mask = [r'\s', line_start_offset - match_start_offset, -1]
                    token_masks.append(whitespace_token_mask)
                    for g_idx, group in enumerate(match_data['groups']):
                        if debug:
                            print("  {}: {:>5}:{:>5}: {:>20}:{:>50}".format(g_idx, group[1], group[2], group[3], group[0]))

                        whitespace_token_mask[2] = group[1]
                        line_regex_token_sequence.push_token(
                            RegexToken(Token.WHITESPACE_HORIZONTAL, len=whitespace_token_mask[2] - whitespace_token_mask[1])
                        )

                        match_token_mask = [r'.', group[1], group[2], group[3]]
                        token_masks.append(match_token_mask)

                        main_regex_token = self.regex_token_sequence.get_token_by_name(group[3])
                        # print("main_regex_token={}".format(main_regex_token))

                        line_regex_token_sequence.push_token(
                            RegexToken(capture_name=match_token_mask[3], token=Token.ANY_CHAR,
                                       len=match_token_mask[2] - match_token_mask[1],
                                       multiline=main_regex_token.multiline))

                        whitespace_token_mask = [r'\s', group[2], -1, '']
                        token_masks.append(whitespace_token_mask)

                    # Last token mask
                    whitespace_token_mask[2] = match_end_offset - match_start_offset
                    line_regex_token_sequence.push_token(
                        RegexToken(Token.WHITESPACE_HORIZONTAL, len=whitespace_token_mask[2] - whitespace_token_mask[1])
                    )

                    match_data['fixed_regex_token_sequence'] = line_regex_token_sequence

                    # Generate the shadow token set so that we can match the following lines
                    line_regex_token_sequence.generate_shadow_token_sequence()
                    if line_regex_token_sequence.shadow_token_sequence is not None:
                        shadow_regex_str = line_regex_token_sequence.shadow_token_sequence.regex_str()
                        if debug:
                            print("Generated ShadowRegex:{}".format(shadow_regex_str))
                        shadow_pattern = re.compile(shadow_regex_str)
                        shadow_token_sequence = line_regex_token_sequence.shadow_token_sequence

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
                                # print("Shadow  :{}".format(shadow_token_sequence.regex_str()))
                                try:
                                    shadow_token_sequence.adjust_alignment(1)
                                    # print("Adjusted:{}".format(shadow_token_sequence.regex_str()))
                                    adjusted_shadow_pattern = re.compile(shadow_token_sequence.regex_str())
                                    shadow_matches_in_line = regex_pattern_apply_on_text(adjusted_shadow_pattern, match_text)
                                    if len(shadow_matches_in_line) > 0:
                                        # print("Adjustment={} Found Match: {}".format(adjustment, match_text))
                                        break
                                except RuntimeError as e:
                                    print(e)
                                    break
                                    
                            shadow_token_sequence.adjust_alignment(-adjustment)

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
class RegexTokenMap:
    token_sequence_map: Dict = field(init=False, default_factory=dict)

    def get_or_create_similar(self, line_item):
        token_hash_key = line_item['token_hash']
        token_sequence = line_item['token_sequence']

        flag_match = False
        for key, token_map_entry in self.token_sequence_map.items():
            group_token_sequence = token_map_entry['group_token_sequence']
            try:
                if group_token_sequence.is_similar(token_sequence):
                    flag_match = True
                    break
            except RuntimeError as e:
                print("Error! LineNum={} line_text={}".format(line_item["num"], line_item["text"]))
                raise e

        if not flag_match:
            token_map_entry = self.create_new_token_map_entry(line_item, token_hash_key)

        return token_map_entry

    def get_or_create_exact(self, line_item):
        token_hash_key = line_item['token_hash']
        if token_hash_key not in self.token_sequence_map:
            self.create_new_token_map_entry(line_item, token_hash_key)

        return self.token_sequence_map[token_hash_key]

    def create_new_token_map_entry(self, line_item, token_hash_key):
        group_token_sequence = copy.deepcopy(line_item['token_sequence'])
        print("New Entry: LineNum:{} group_token_sequence='{}'".format(line_item['num'], group_token_sequence.token_str()))
        # TBD: This happens in case line has no char. Need to check if we should assign a token
        if group_token_sequence.token_str() == '':
            print(group_token_sequence)

        self.token_sequence_map[token_hash_key] = {'group_token_sequence': group_token_sequence, 'line_items': []}
        return self.token_sequence_map[token_hash_key]

    def get_or_create_entry(self, line_item, strategy='exact'):
        if strategy == 'exact':
            token_map_entry = self.get_or_create_exact(line_item)
        elif strategy == 'similar':
            token_map_entry = self.get_or_create_similar(line_item)
        else:
            raise RuntimeError("strategy '{}' not supported".format(strategy))

        group_token_sequence = token_map_entry['group_token_sequence']
        item_token_sequence = line_item['token_sequence']

        try:
            for token_index in range(len(group_token_sequence.tokens)):
                # This will happen when group_token_sequnce has a tail WS token
                if token_index >= len(item_token_sequence.tokens):
                    group_token = group_token_sequence.tokens[token_index]
                    if group_token.is_whitespace():
                        break
                    else:
                        raise RuntimeError("The token_map_entry {} has an extra token {}".format(token_map_entry, group_token))

                if group_token_sequence.tokens[token_index].min_len > item_token_sequence.tokens[token_index].min_len:
                    group_token_sequence.tokens[token_index].min_len = item_token_sequence.tokens[token_index].min_len
                if group_token_sequence.tokens[token_index].max_len < item_token_sequence.tokens[token_index].max_len:
                    group_token_sequence.tokens[token_index].max_len = item_token_sequence.tokens[token_index].max_len
        except IndexError as e:
            print("IndexError:")
            print("group_token_sequence:{}".format(group_token_sequence.token_str()))
            print(" item_token_sequence:{}".format(item_token_sequence.token_str()))

        return token_map_entry

    # TBD: Check how to create an iterator class
    def items(self):
        return self.token_sequence_map.items()


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

        regex_line_token_seq = RegexTokenSequence(flag_full_line=True)

        if debug:
            print("Generate Tokens:")
        for token, value in self.generate_tokens(line_text):
            if debug:
                print("Token Match:{} Value={}".format(token, value))
            regex_line_token_seq.push_token(token)

        # Create regex from generated tokens
        line_regex_str = regex_line_token_seq.regex_str()

        matches = regex_apply_on_text(line_regex_str, line_text)['matches']
        if len(matches) > 0:
            if debug:
                print("The regex generation is successful")
                print(matches)
        else:
            if debug:
                print("Regex Str:{}".format(regex_line_token_seq.regex_str()))
                print("Tokens Str:{}".format(regex_line_token_seq.token_str()))
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

    def generate_token_hash_map(self, text):
        # TBD: This can be class
        token_hash_map = RegexTokenMap()

        for line_item in self.generate_regex_token_hashes_from_text(text):
            token_hash_map_entry = token_hash_map.get_or_create_entry(line_item, strategy='similar')

            # This needs to be moved to assimilate token
            token_hash_map_entry['line_items'].append(line_item)

        return token_hash_map


def build_and_apply_regex(text, build_all=False, extrapolate=False):
    regex_dictionary = RegexDictionary()
    regex_generator = RegexGenerator(regex_dictionary)

    print("Regex Token Sequences:")
    for line_item in regex_generator.generate_regex_token_sequence_per_line_from_text(text):
        print("{}:{}".format(line_item['num'], line_item['token_sequence'].token_str()))

    print("Regex Token Hashes:")
    for line_item in regex_generator.generate_regex_token_hashes_from_text(text):
        print("{}:{}".format(line_item['num'], line_item['token_hash']))

    print("Regex Token Hashmap:")
    token_hash_map = regex_generator.generate_token_hash_map(text)
    result = None
    color_index = 0
    for token_hash_key, token_hash_matches in token_hash_map.items():
        item_count = len(token_hash_matches['line_items'])
        # group_regex_str = token_hash_matches['group_token_sequence'].regex_str()
        group_regex_str = token_hash_matches['group_token_sequence'].generate_named_token_sequence().regex_str()

        token_hash_regex_match_result = regex_apply_on_text(group_regex_str, text, flags={"multiline": 1})
        regex_match_count = len(token_hash_regex_match_result['matches'])

        token_hash_key_token_count = len(token_hash_matches['group_token_sequence'].tokens)
        token_hash_key_sample_count = len(token_hash_matches['line_items'])

        # Sampled for debugging. token_hash_key_count to be removed when sampling finished.
        # if item_count != regex_match_count and token_hash_key == "S-D2-S-P-S-W-S-D2-S-N-S-N":
        # TBD: This condition we should be able to send from frontend
        # if "D2" in token_hash_key:
        if build_all or token_hash_key_token_count > 10:
            print("{:<30}[{:>3}]".format("'{}'[{}]".format(token_hash_key, len(token_hash_key)),
                                         token_hash_key_sample_count))
            print("    group_token_sequence:{}".format(token_hash_matches['group_token_sequence'].token_str()))
            print("    group_regex_str={}".format(group_regex_str))
            print("Sample Count={:>4}".format(token_hash_key_sample_count))
            print(" Match Count={:>4}".format(len(token_hash_regex_match_result['matches'])))

            for match in token_hash_regex_match_result['matches']:
                match['match'].append(regex_generator.regex_colors[color_index].value)

                for group in match['groups']:
                    group.insert(3, regex_generator.regex_colors[color_index].value)

            color_index = (color_index + 1) % len(regex_generator.regex_colors)

            if result is None:
                result = token_hash_regex_match_result
            else:
                result['matches'].extend(token_hash_regex_match_result['matches'])

    return result
