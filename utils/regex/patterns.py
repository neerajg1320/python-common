import re

# Used to match a valid string in regex comment pattern
REGEX_COMMENT_PATTERN_ESCAPED = r"^\(\?#.*\)$"

# Used only for display purpose like in error handling
REGEX_COMMENT_PATTERN = r"^(?#.*)$"


def is_regex_comment_pattern(text):
    # We allow the newlines as well
    return len(re.findall(REGEX_COMMENT_PATTERN_ESCAPED, text, flags=re.DOTALL)) == 1


def is_whitespace(text):
    return re.match(r'^\s*$', text) is not None


def get_regex_comment_pattern():
    return REGEX_COMMENT_PATTERN
