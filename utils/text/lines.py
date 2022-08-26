import re
import copy
from collections import OrderedDict


def get_text_shape(text):
    text_shape = {"lines": OrderedDict()}
    lines = text.splitlines()
    for index, line in enumerate(lines):
        text_shape["lines"][index] = len(line)

    text_shape["count"] = len(lines)

    return text_shape


# Given a string buffer return the max line length
def get_max_line_length(text):
    max_len = 0
    if text is not None:
        for line in text.splitlines():
            line_len = len(line)
            if line_len > max_len:
                max_len = line_len

    return max_len


def pad_lines(text, length, padding_char=' ', join_char="\n"):
    buffer = ""
    for line in text.splitlines():
        padded_line = line.ljust(length, padding_char)
        buffer = join_char.join([buffer, padded_line])

    return buffer


def is_whitespace(inp_str):
    return re.match(r'^\s*$', inp_str) is not None


def get_multiline_post_para_offsets(matches, end_offset):
    matches_post_para_with_offsets = []

    prev_m = None
    for m in matches:
        # print(m)

        full_match = m['match']
        full_match_start = full_match[1]

        if prev_m is not None:
            prev_full_match = prev_m['match']
            prev_full_match_end = prev_full_match[2]
            unmatched_text_offsets = (prev_full_match_end, full_match_start)
            prev_m['post_para'] = unmatched_text_offsets

        m_rel_groups = {'match': full_match, 'groups': []}

        groups = m['groups']
        for index, g in enumerate(groups):
            # print('  group[{}]={}'.format(index, g))
            g_rel = copy.deepcopy(g)
            g_rel[1] -= full_match_start
            g_rel[2] -= full_match_start
            # print('  g_rel[{}]={}'.format(index, g_rel))
            g_rel.append(full_match_start)
            g_rel.append(full_match_start) # This will be different in case of post_para groups

            m_rel_groups['groups'].append(g_rel)

        matches_post_para_with_offsets.append(m_rel_groups)

        # print(m_rel_groups)
        prev_m = m_rel_groups

    # print(matches_post_para_with_offsets)
    if prev_m is not None:
        prev_full_match = prev_m['match']
        prev_full_match_end = prev_full_match[2]
        unmatched_text_offsets = (prev_full_match_end, end_offset)
        prev_m['post_para'] = unmatched_text_offsets

    return matches_post_para_with_offsets


def get_matches_with_group_relative_offsets(input_str, matches_with_para,
                                            ignore_post_first=True,
                                            blank_line_threshold=1):
    matches_with_post_groups = copy.deepcopy(matches_with_para)

    for m_idx,m in enumerate(matches_with_post_groups):
        # print(m)
        groups = m['groups']
        # print(groups)

        post_para_offsets = m['post_para']
        buffer_start_offset_for_post_para = post_para_offsets[0]
        post_para_str = input_str[buffer_start_offset_for_post_para:post_para_offsets[1]]

        # Necessary to avoid circular import
        from utils.regex_utils import regex_apply_on_text

        # We should not put \n in the pattern as the last line in buffer might not be having one
        line_matches = regex_apply_on_text("^.*$", post_para_str, flags={'multiline': True})['matches']

        m['post_groups_list'] = []

        # Skip the first line and then carve the strings out of the second line onwards
        blank_lines_count = 0
        for index, line_match in enumerate(line_matches):
            line = line_match['match'][0]
            post_para_start_offset_for_line = line_match['match'][1]
            buffer_start_offset_for_line = post_para_start_offset_for_line + buffer_start_offset_for_post_para

            # We assume the first line is remaining part of the matched line
            if ignore_post_first and index == 0:
                continue

            if is_whitespace(line):
                blank_lines_count += 1

                # If blank_lines count exceeds acceptance threshold then we need to break
                # This will happen on the last row in a para or on a page
                if blank_lines_count > blank_line_threshold:
                    break

                continue
            else:
                blank_lines_count = 0

            groups_post_para = []
            for g in groups:
                g_name = g[3]
                g_name_parts = g_name.split("__")
                if len(g_name_parts) > 1 and g_name_parts[1].upper() == "M":
                    g_post_para = copy.deepcopy(g)
                    g_post_para[0] = line[g_post_para[1]:g_post_para[2]]
                    g_post_para[5] = buffer_start_offset_for_line

                    groups_post_para.append(g_post_para)

            # print(groups_post_para)
            if len(groups_post_para) > 0:
                m['post_groups_list'].append(groups_post_para)

    return matches_with_post_groups


def print_matches_with_post_groups(matches):
    for index,m in enumerate(matches):
        print('match[{}]'.format(index))
        print('groups: {}'.format(m['groups']))
        print('post_groups_list:')
        for pg_idx,p_grpups in enumerate(m['post_groups_list']):
            print('  p_groups[{}]: {}'.format(pg_idx, p_grpups))


def set_groups_absolute_offset(matches):
    matches_absolute = copy.deepcopy(matches)

    for m in matches_absolute:
        for g in m['groups']:
            g[1] += g[5]
            g[2] += g[5]

    return matches_absolute


def extend_match_groups_with_post_groups(matches):
    matches_extended = copy.deepcopy(matches)

    for m in matches_extended:
        m_extended = {'groups': m['groups']}

        for post_groups in m['post_groups_list']:
            m_extended['groups'].extend(post_groups)

    return matches_extended


# After combining: The offsets have not much meaning
# we get a joined string along wit group name
def combine_matches_with_post_groups(matches, join_str="\n", add_blank_post_groups=False, debug=False):
    # print_matches_with_post_groups(matches)
    matches_combined = []
    for m in matches:
        m_combined = {'groups': []}

        groups_map ={}
        for g_idx,group in enumerate(m['groups']):
            c_group = {}
            c_group['text'] = group[0]
            c_group['name'] = group[3]
            c_group['offsets_list'] = [[group[1], group[2]]]
            m_combined['groups'].append(c_group)

            groups_map[c_group['name']] = c_group

        for post_groups in m['post_groups_list']:
            # print(post_groups)
            for pg in post_groups:
                c_group = groups_map[pg[3]]

                if is_whitespace(pg[0]):
                    if debug:
                        print("Ignored:post group for '{}' is blank".format(c_group['name']))
                else:
                    c_group['text'] = join_str.join([c_group['text'], pg[0]])
                    c_group['offsets_list'].append([pg[1], pg[2]])

        matches_combined.append(m_combined)

    return matches_combined


def print_combined_matches(matches):
    for m_idx,m in enumerate(matches):
        print("match[{}]".format(m_idx))
        for g_idx,g in enumerate(m['groups']):
            print("group[{}:{}]:\n{}\n{}".format(g_idx, g['name'], g['text'], g['offsets_list']))
