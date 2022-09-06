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
