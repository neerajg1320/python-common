import re
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


def is_blank_line(inp_str):
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
            g_rel = g.copy()
            g_rel[1] -= full_match_start
            g_rel[2] -= full_match_start
            # print('  g_rel[{}]={}'.format(index, g_rel))
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


def get_matches_with_post_groups(input_str, matches_with_para):
    matches_with_post_groups = matches_with_para.copy()

    for m in matches_with_post_groups:
        # print(m)
        groups = m['groups']
        # print(groups)

        post_para_offsets = m['post_para']
        post_para_str = input_str[post_para_offsets[0]:post_para_offsets[1]]
        # print(post_para_str)
        lines = post_para_str.splitlines()

        m['post_groups_list'] = []

        # Skip the first line and then carve the strings out of the second line onwards
        for index, line in enumerate(lines):
            # We assume the first line is remaining part of the matched line
            if index == 0:
                continue
            if is_blank_line(line):
                continue
            groups_post_para = []
            for g in groups:
                g_post_para = g.copy()
                g_post_para[0] = line[g_post_para[1]:g_post_para[2]]
                groups_post_para.append(g_post_para)
            # print(groups_post_para)
            m['post_groups_list'].append(groups_post_para)

        # print(m)
    return matches_with_post_groups


def print_matches_with_post_groups(matches):
    for index,m in enumerate(matches):
        print('match[{}]'.format(index))
        print('groups: {}'.format(m['groups']))
        for pg_idx,p_grpups in enumerate(m['post_groups_list']):
            print('p_groups[{}]: {}'.format(pg_idx, p_grpups))


# After combining: The offsets have not much meaning
# we get a joined string along wit group name
def combine_matches_with_post_groups(matches):
    # print_matches_with_post_groups(matches)
    matches_combined = []
    for m in matches:
        m_combined = {'groups': []}

        groups = m['groups']
        for g_idx,group in enumerate(groups):
            c_group = {}
            c_group['text'] = group[0]
            c_group['name'] = group[3]

            for post_groups in m['post_groups_list']:
                # print(post_groups)
                pg = post_groups[g_idx]
                c_group['text'] = "\n".join([c_group['text'], pg[0]])

            m_combined['groups'].append(c_group)

        matches_combined.append(m_combined)
        # print(m_combined)

    return matches_combined

