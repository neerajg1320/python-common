from utils.datetime_utils import get_isoformat_date_str_from_datetime


def security_symbol(sec):
    if sec['securityType'] != "EQ":
        extra_str = "_{}".format(get_isoformat_date_str_from_datetime(sec['expiryDate']))
        if sec['securityType'] == "OPT":
            extra_str += "_{}".format(sec['optionType'])
            stk = sec['optionStrike']
            extra_str += "_{}".format(int(stk) if int(stk) == stk else  round(stk, 2))
    else:
        extra_str = ""

    return "{}_{}{}".format(sec['securityName'], sec['securityType'],  extra_str)


def print_transaction(tx, title=None):
    if title:
        print(title)
    print("{: >6} {} {: >25} {: >7}  {:12.2f}  {:16.2f} {:16.2f} {:16.2f}".format(
        "{:6d}".format(tx['id']) if 'id' in tx else '<>',
        tx['transactionDate'],
        tx['securityName'],
        tx['tradeType'],
        tx['quantity'],
        tx['grossAmount'],
        tx['brokerage'],
        tx['netAmount']
    ))

def print_openpos(openpos, title=None):
    if title:
        print(title)
    print("{: >6} {: >25}[{}]{}  {:12.2f}  {: >7}  {}  {: >5}  {: >18}".format(
        "{:6d}".format(openpos['id']) if 'id' in openpos else '<>',
        openpos['securityName'].replace(' ', '.'),
        len(openpos['securityName']),
        security_symbol(openpos),
        openpos['quantity'],
        openpos['openTradeType'],
        openpos['openTradeDate'],
        str(openpos['openTradeSplit']),
        "{:16.2f}".format(
            openpos['proceeds'] if openpos['openTradeType'] == 'SELL' else openpos['costBasis']
        ),
    ))

def print_closedpos(closedpos, title=None):
    if title:
        print(title)

    # The following print style causes hard to debug problems when some values are None
    print("{: >6} {: >25}  {:12.2f} {:16.2f} {:16.2f} {:16.2f} {: >7}  {}  {: >5} {: >7}  {}  {: >5} {:5d} days".format(
        "{:6d}".format(closedpos['id']) if 'id' in closedpos else '<>',
        closedpos['securityName'],
        closedpos['quantity'],
        closedpos['proceeds'],
        closedpos['costBasis'],
        closedpos['netGain'],
        closedpos['openTradeType'],
        closedpos['openTradeDate'],
        str(closedpos['openTradeSplit']),
        closedpos['closeTradeType'],
        closedpos['closeTradeDate'],
        str(closedpos['closeTradeSplit']),
        closedpos['duration']
    ))


def closed_pos_summary(closedpos):
    return [ closedpos['proceeds'], closedpos['costBasis'], closedpos['netGain'] ]

