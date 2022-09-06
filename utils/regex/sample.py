import pandas as pd
from .builder import Alignment, Token, RegexToken, CompositeToken, NamedToken, RegexTokenSequence, RegexTextProcessor


def get_sample_hdfc_regex_token_sequence(debug=False):
    token_sequence = RegexTokenSequence(flag_full_line=True)

    # To be used in Debit and Credit where the value is blank as only one of Credit or Debit is specified
    blank_token = RegexToken(token=Token.WHITESPACE_HORIZONTAL, len=1)

    # We have a starting space
    token_sequence.push_token(blank_token)

    token_sequence.push_token(NamedToken(RegexToken(token=Token.DATE_YY), "TransactionDate"))
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _max_len=1))
    token_sequence.push_token(
        NamedToken(RegexToken(token=Token.PHRASE, _max_len=1, multiline=True, alignment=Alignment.LEFT), "Description"))
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=10, _max_len=90))
    token_sequence.push_token(NamedToken(RegexToken(token=Token.WORD, _min_len=15, _max_len=16), "ReferenceNum"))
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _max_len=1))
    token_sequence.push_token(NamedToken(RegexToken(token=Token.DATE_YY), "ValueDate"))
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=20, _max_len=36))

    # Debit token is an integer or a blank_token.
    debit_token = RegexToken(token=Token.NUMBER, _min_len=1, _max_len=20)
    debit_token_optional = NamedToken(CompositeToken(debit_token, blank_token), "Debit")
    token_sequence.push_token(debit_token_optional)

    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=10, _max_len=27))

    # Debit token is an integer or a blank_token.
    credit_token = RegexToken(token=Token.NUMBER, _min_len=1, _max_len=20)
    credit_token_optional = NamedToken(CompositeToken(credit_token, blank_token), "Credit")
    token_sequence.push_token(credit_token_optional)

    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=15, _max_len=30))
    token_sequence.push_token(NamedToken(RegexToken(token=Token.NUMBER, _min_len=1, _max_len=20), "Balance"))

    # We have a trailing space
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=0, _max_len=4))

    if debug:
        print("Regex Builder:")
        print(token_sequence)

    return token_sequence


def apply_regex_token_sequence(token_sequence, text):
    regex_text_processor = RegexTextProcessor(token_sequence)
    regex_text_processor.data = text

    regex_text_processor.process()

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

    regex_text_processor.generate_matches_absolute()
    for index, line_final in enumerate(regex_text_processor.matches_with_absolute_offsets[sample_offset:sample_size]):
        print(line_final)

    regex_text_processor.generate_frame_objects(shadow_trim=True)

    df = pd.DataFrame(regex_text_processor.frame_objects)
    print("DataFrame:")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', None)
    print(df)

    print("Total Matches: {}".format(len(regex_text_processor.matched_lines_data)))
    return regex_text_processor
