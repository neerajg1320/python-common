from .builder import Token, RegexToken, CompositeToken, NamedToken, RegexBuilder


def create_sample_hdfc_builder(debug=False):
    regex_builder = RegexBuilder()

    regex_builder.push_token(NamedToken(RegexToken(token=Token.DATE_YY), "TransactionDate"))
    regex_builder.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, max_len=1))
    regex_builder.push_token(NamedToken(RegexToken(token=Token.PHRASE, max_len=1), "Descript__M__LA"))
    regex_builder.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=10, max_len=90))
    regex_builder.push_token(NamedToken(RegexToken(token=Token.WORD, min_len=15, max_len=16), "ReferenceNum"))
    regex_builder.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, max_len=1))
    regex_builder.push_token(NamedToken(RegexToken(token=Token.DATE_YY), "ValueDate"))
    regex_builder.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=20, max_len=34))

    # To be used in Debit and Credit where the value is blank as only one of Credit or Debut is specified
    blank_token = RegexToken(token=Token.WHITESPACE_HORIZONTAL, len=1)

    debit_token = RegexToken(token=Token.NUMBER, min_len=1, max_len=20)
    debit_token_optional = NamedToken(CompositeToken(debit_token, blank_token), "Debit")
    regex_builder.push_token(debit_token_optional)

    regex_builder.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=10, max_len=25))

    credit_token = RegexToken(token=Token.NUMBER, min_len=1, max_len=20)
    credit_token_optional = NamedToken(CompositeToken(credit_token, blank_token), "Credit")
    regex_builder.push_token(credit_token_optional)

    regex_builder.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=15, max_len=30))
    regex_builder.push_token(NamedToken(RegexToken(token=Token.NUMBER, min_len=1, max_len=20), "Balance"))

    if debug:
        print("Regex Builder:")
        print(regex_builder)

    return regex_builder
