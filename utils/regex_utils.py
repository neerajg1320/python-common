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


def regex_apply_on_text_extrapolate(regex_str, text, flags=None, extrapolate=False, debug=False):
    result = regex_apply_on_text(regex_str, text, flags=flags)

    if extrapolate:
        extrapolate_new_approach = False

        if not extrapolate_new_approach:
            multiline_matches = get_multiline_post_para_offsets(result['matches'], len(text))

            matches_with_post_groups = get_matches_with_group_relative_offsets(text, multiline_matches)

            if debug:
                print("Matches with post groups")
                for m in matches_with_post_groups:
                    print(m)

            matches_with_extended_groups = extend_match_groups_with_post_groups(matches_with_post_groups)

            if debug:
                print("Matches with extended groups")
                for m in matches_with_extended_groups:
                    print(m)

            matches_with_absolute_offsets = set_groups_absolute_offset(matches_with_extended_groups)

            if debug or True:
                logger.info("multiline_matches with absolute offsets:{}".format(matches_with_absolute_offsets))

            result['matches'] = matches_with_absolute_offsets
        else:
            # Import for testing. Later we will have construct
            from utils.regex.sample import get_sample_hdfc_regex_token_set
            from utils.regex.builder import RegexTextProcessor

            regex_processor = RegexTextProcessor(get_sample_hdfc_regex_token_set())
            regex_processor.data = text

            regex_processor.process()
            regex_processor.generate_matches_absolute()
            result['matches'] = regex_processor.matches_with_absolute_offsets

    # Added for unit testing. Can be removed
    flag_add_color = False
    if flag_add_color:
        for index, match in enumerate(result['matches']):
            match['match'].append('rgb({}, 108, 222)'.format(38 + 50 * index))

    return result


def regex_apply_on_text(regex_str, text, flags=None):
    pattern, regex_error = check_compile_regex(regex_str, flags=flags)

    if not regex_error:
        matches = regex_pattern_apply_on_text(pattern, text)

    return {"matches": matches, "error": regex_error}


def regex_pattern_apply_on_text(regex_pattern, text):
    groups_dict = dict(regex_pattern.groupindex)

    matches = []
    for m in regex_pattern.finditer(text):
        match_object = [text[m.start():m.end()], m.start(), m.end()]
        groups_object = get_group_offsets(text, m, groups_dict)
        matches.append({"match": match_object, "groups": groups_object})

    return matches


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
