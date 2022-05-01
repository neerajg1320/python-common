import re
from utils.exceptions import InvalidParams


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
