import re
from utils.exceptions import InvalidParams
from utils.text.lines import get_multiline_post_para_offsets, get_matches_with_group_relative_offsets,\
    combine_matches_with_post_groups, print_combined_matches, print_matches_with_post_groups, \
    extend_match_groups_with_post_groups, set_groups_absolute_offset
import logging


logger = logging.getLogger(__name__)


# Ref:
# https://stackoverflow.com/questions/19630994/how-to-check-if-a-string-is-a-valid-regex-in-python
#
def check_compile_regex(regex_str, flags=None):
    pattern = None
    error = None

    re_flags = 0
    if flags is not None:
        re_flags |= re.MULTILINE if flags.get('multiline', False) else 0
        re_flags |= re.DOTALL if flags.get('dotall', False) else 0

    try:
        pattern = re.compile(regex_str, re_flags)
    except re.error as e:
        error = str(e)

    return pattern, error


def regex_apply_on_text_extrapolate(regex_str, text, flags=None, extrapolate=False):
    result = regex_apply_on_text(regex_str, text, flags=flags)

    if extrapolate:
        multiline_matches = get_multiline_post_para_offsets(result['matches'], len(text))

        matches_with_post_groups = get_matches_with_group_relative_offsets(text, multiline_matches)
        matches_with_extended_groups = extend_match_groups_with_post_groups(matches_with_post_groups)
        matches_with_absolute_offsets = set_groups_absolute_offset(matches_with_extended_groups)

        logger.info("multiline_matches with absolute offsets:{}".format(matches_with_absolute_offsets))

        result['matches'] = matches_with_absolute_offsets

    return result


def regex_apply_on_text(regex_str, text, flags=None):
    pattern, regex_error = check_compile_regex(regex_str, flags=flags)

    # debug_log("groups_dict=", groups_dict)

    matches = []
    if not regex_error:
        groups_dict = dict(pattern.groupindex)
        for m in pattern.finditer(text):
            # debug_log("m.groups()=", m.groups())
            match_object = [text[m.start():m.end()], m.start(), m.end()]
            groups_object = get_group_offsets(text, m, groups_dict)
            matches.append({"match": match_object, "groups": groups_object})
            # matches.append([text[m.start():m.end()], m.start(), m.end()])

    return {"matches": matches, "error": regex_error}


def get_group_offsets(text, match, groups_dict):
    groups = match.groups()
    reverse_group_dict = {v:k for k,v in groups_dict.items()}

    result = []
    for index in range(1, len(groups)+1):
        group_start, group_end = match.span(index)
        group_text = match.group(index)
        title = reverse_group_dict[index] if index in reverse_group_dict else str(index)
        result.append([group_text, group_start, group_end, title])

    # debug_log(result)
    return result

def regex_create_html(regex_str, text, flags=None):
    pattern, regex_error = check_compile_regex(regex_str, flags=flags)

    if regex_error is not None:
        raise InvalidParams('Regex Error: ' + regex_error)

    matches = pattern.findall(text)
    return matches
