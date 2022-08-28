from .builder import Token, RegexToken, CompositeToken, NamedToken, RegexTokenSet, RegexAnalyzer


def sample_hdfc_regex_token_set(debug=False):
    regex_token_set = RegexTokenSet(flag_full_line=True)

    # To be used in Debit and Credit where the value is blank as only one of Credit or Debit is specified
    blank_token = RegexToken(token=Token.WHITESPACE_HORIZONTAL, len=1)

    # We have a starting space
    regex_token_set.push_token(blank_token)

    regex_token_set.push_token(NamedToken(RegexToken(token=Token.DATE_YY), "TransactionDate"))
    regex_token_set.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _max_len=1))
    regex_token_set.push_token(NamedToken(RegexToken(token=Token.PHRASE, _max_len=1), "Descript__M__LA"))
    regex_token_set.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=10, _max_len=90))
    regex_token_set.push_token(NamedToken(RegexToken(token=Token.WORD, _min_len=15, _max_len=16), "ReferenceNum"))
    regex_token_set.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _max_len=1))
    regex_token_set.push_token(NamedToken(RegexToken(token=Token.DATE_YY), "ValueDate"))
    regex_token_set.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=20, _max_len=36))

    # Debit token is an integer or a blank_token.
    debit_token = RegexToken(token=Token.NUMBER, _min_len=1, _max_len=20)
    debit_token_optional = NamedToken(CompositeToken(debit_token, blank_token), "Debit")
    regex_token_set.push_token(debit_token_optional)

    regex_token_set.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=10, _max_len=27))

    # Debit token is an integer or a blank_token.
    credit_token = RegexToken(token=Token.NUMBER, _min_len=1, _max_len=20)
    credit_token_optional = NamedToken(CompositeToken(credit_token, blank_token), "Credit")
    regex_token_set.push_token(credit_token_optional)

    regex_token_set.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=15, _max_len=30))
    regex_token_set.push_token(NamedToken(RegexToken(token=Token.NUMBER, _min_len=1, _max_len=20), "Balance"))

    # We have a trailing space
    regex_token_set.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, _min_len=0, _max_len=4))

    if debug:
        print("Regex Builder:")
        print(regex_token_set)

    return regex_token_set


def sample_hdfc_analyzer(regex_token_set, text):
    regex_analyzer = RegexAnalyzer(regex_token_set)

    regex_analyzer.data = text

    data = regex_analyzer.get_matches_with_regex_token_set()

    sample_offset = 0
    sample_size = 10
    sample_data = data[sample_offset:sample_size]

    for index, line_matches in enumerate(sample_data):
        for l_match in line_matches:
            print("[{:>4}]  LineNum:{}".format(index, l_match['line_num']))
            print("    Match: {}".format(l_match['match']))
            print("    Groups: {}".format(l_match['groups']))
            # print("    FixedRegexTokenSet: {}".format(l_match['fixed_regex_token_set']))
            print("    FixedRegex:{}".format(l_match['fixed_regex_token_set'].regex_str()))

    print("The Mask Map:")
    for index, line_matches in enumerate(sample_data):
        for l_match in line_matches:
            print("{:>4}: {}".format(index, l_match['fixed_regex_token_set'].mask_str()))
            print("{:>4}: {}".format(index, l_match['fixed_regex_token_set'].shadow_token_set.mask_str()))

    print("The Text Lines:")
    for index, line_matches in enumerate(sample_data):
        for l_match in line_matches:
            print("{:>4}: {}".format(index, l_match['match'][0]))

    print("The Token Lengths Map:")
    for index, line_matches in enumerate(sample_data):
        for l_match in line_matches:
            print("{}".format(l_match['fixed_regex_token_set'].token_type_len_str()))
    # The next stage we will fix the alignment for the columns

    return regex_analyzer
