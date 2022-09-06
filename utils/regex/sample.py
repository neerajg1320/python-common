import pandas as pd
from .builder import Alignment, Token, RegexToken, CombineOperator, \
    NamedToken, RegexTokenSequence, RegexTextProcessor


def get_sample_hdfc_regex_token_sequence(debug=False):
    token_sequence = RegexTokenSequence(flag_full_line=True)

    # To be used in Debit and Credit where the value is blank as only one of Credit or Debit is specified
    blank_token = RegexToken(token=Token.WHITESPACE_HORIZONTAL, len=1)

    # We have a starting space
    token_sequence.push_token(blank_token)

    token_sequence.push_token(NamedToken("TransactionDate", token=Token.DATE_YY))
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, max_len=1))
    token_sequence.push_token(NamedToken("Description", token=Token.PHRASE, max_len=1, multiline=True,
                                         alignment=Alignment.LEFT))
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=10, max_len=90))
    token_sequence.push_token(NamedToken("ReferenceNum", token=Token.WORD, min_len=15, max_len=16))
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, max_len=1))
    token_sequence.push_token(NamedToken("ValueDate", token=Token.DATE_YY))
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=20, max_len=36))

    # Debit token is an integer or a blank_token.
    debit_token = RegexToken(token=Token.NUMBER, min_len=1, max_len=20)
    debit_token_optional = NamedToken("Debit", token=RegexToken(components=[debit_token, blank_token],
                                                                operator=CombineOperator.OR))
    token_sequence.push_token(debit_token_optional)

    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=10, max_len=27))

    # Debit token is an integer or a blank_token.
    credit_token = RegexToken(token=Token.NUMBER, min_len=1, max_len=20)
    credit_token_optional = NamedToken("Credit", token=RegexToken(components=[credit_token, blank_token],
                                                                  operator=CombineOperator.OR))
    token_sequence.push_token(credit_token_optional)

    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=15, max_len=30))
    token_sequence.push_token(NamedToken("Balance", token=Token.NUMBER, min_len=1, max_len=20))

    # We have a trailing space
    token_sequence.push_token(RegexToken(token=Token.WHITESPACE_HORIZONTAL, min_len=0, max_len=4))

    if debug:
        print("Regex Builder:")
        print(token_sequence)

    return token_sequence
