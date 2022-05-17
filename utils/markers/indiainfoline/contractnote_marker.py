import dateutil


##
# TradeNum: 7 - digits
# TradeTime: is not followed by (OPT|FUT)(STK|IDX)
#
indiainfoline_eq_regex = r"""(?#
)^(?#
)\s*(?P<OrderNum>\d{16})(?#
)\s+(?P<OrderTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?P<TradeNum>\d{7,8})(?#
)\s+(?P<TradeTime>\d{2}:\d{2}:\d{2})(?!\s+(?:OPT|FUT)(?:STK|IDX))(?#
)\s+(?P<SecurityName>[\w\s\-\.]{1,32})(?#
)\s+(?:(?P<Exchange>\w{3})\s-\s(?P<TradeType>\w{3,4}))(?#
)\s+(?P<Quantity>[-]?\d+)(?#
)\s+(?P<PricePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?:(?P<BrokeragePerUnit>\d+(?:\.\d+)?)|[-]*)(?#
)\s+(?P<NetRatePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?P<NetTotal>[-]?\d+(?:\.\d+)?)(?#
)(?P<Tail>.*)(?#
)$(?#
)"""


##
# TradeNum: 8 - digits
# SecurityName - follows (OPT|FUT)(STK|IDX)
#
indiainfoline_fno_regex = r"""(?#
)^(?#
)\s*(?P<OrderNum>\d{16})(?#
)\s+(?P<OrderTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?P<TradeNum>\d{7,8})(?#
)\s+(?P<TradeTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?P<SecurityType>OPT|FUT)(?P<SymbolType>STK|IDX)(?#
    )\s(?P<SecurityName>[\w\s\-\.]{1,26})(?#
)\s+(?:(?P<Exchange>\w{3})\s-\s(?P<TradeType>\w{3,4}))(?#
)\s+(?P<Quantity>[-]?\d+)(?#
)\s+(?P<PricePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?:(?P<BrokeragePerUnit>\d+(?:\.\d+)?)|[-]*)(?#
)\s+(?P<NetRatePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?P<NetTotal>[-]?\d+(?:\.\d+)?)(?#
)(?P<Tail>.*)(?#
)$\n(?#
)(^\s*(?P<SecurityName2>[\.\w]+(?: \w+)?)\s*$)?(?#
)"""


def indiainfoline_post_process_common(df, metadata=None, action_debug=False):
    df.loc[df['TradeType'] == 'Buy', 'TradeType'] = 'BUY'
    df.loc[df['TradeType'] == 'Sell', 'TradeType'] = 'SELL'
    return df


def indiainfoline_post_process_eq_df(df, metadata=None, action_debug=False):
    df = indiainfoline_post_process_common(df)
    df['SecurityType'] = "EQ"
    df['SecurityName'] = df['SecurityName'].str.strip()
    return df


def indiainfoline_post_process_fno_df(df, metadata=None, action_debug=False):
    df = indiainfoline_post_process_common(df)

    if df['SecurityName2'].isnull().sum() < df['SecurityName2'].shape[0]:
        df['SecurityName2'] = df['SecurityName2'].fillna('')
        df['SecurityName'] = df['SecurityName'] + ' ' + df['SecurityName2']

    df['SecurityName'] = df['SecurityName'].str.strip()

    # If it is a futures then add two spaces, this will make sure that split generates our fields
    df.loc[df['SecurityName'].str.fullmatch(r'[\S]*\s{1,2}[\S]*'), 'SecurityName'] = df['SecurityName'] + " " + " "

    df[['SecurityName', 'ExpirationDate', 'OptionStrike', 'OptionType']] = df['SecurityName'].str.split(' ', expand=True)
    df['ExpirationDate'] = df['ExpirationDate'].apply(lambda x: str(dateutil.parser.parse(x).date()))
    return df


def get_indiainfoline_markers():
    return [
        {
            "type": "EQ",
            "regex": indiainfoline_eq_regex,
            "post_extraction": indiainfoline_post_process_eq_df,
            "suffix": "EQ Trades",
            "excel": True
        },
        {
            "type": "FnO",
            "regex": indiainfoline_fno_regex,
            "post_extraction": indiainfoline_post_process_fno_df,
            "suffix": "FnO Trades",
            "excel": True
        }
    ]
