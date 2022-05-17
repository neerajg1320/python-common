import dateutil
# from utils.dataframe_utils import df_print


# String not preceeded by or following by
# https://javascript.info/regexp-lookahead-lookbehind
# Lookahead is helpful in cases where we want 30$ and not 30 or reverse
# Lookbehind is helpful in cases where we want $30 and not 30 or reverse

# String not beginning with OPT
# https://stackoverflow.com/questions/2116328/regexp-matching-string-not-starting-with-my

axisdirect_eq_regex = r"""(?# https://regex101.com/r/fhGc5I/4
)(?P<OrderNum>\d{16})(?#
)\s+(?P<OrderTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?P<TradeNum>\d{8})[*]*(?#
)\s+(?P<TradeTime>\d{2}:\d{2}:\d{2})(?!\s+(?:OPT|FUT)(?:STK|IDX))(?#
)\s+(?P<SecurityName>[\.\w \-]{1,22})(?#
)\s+(?P<TradeType>B|S)(?#
)\s+(?P<Quantity>[-]?\d+)(?#
)\s+(?P<PricePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?P<BrokeragePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?P<NetRatePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?P<NetTotal>[-]?\d+(?:\.\d+)?)(?#
)"""

## We are matching a multiline pattern
#  SecurityName2 is in second line
axisdirect_fno_regex = r"""(?#
)^(?#
)\s*(?P<OrderNum>\d{9,19})(?#
)\s+(?P<OrderTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?P<TradeNum>\d{5,9})[*]*(?#
)\s+(?P<TradeTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?P<SecurityType>OPT|FUT)(?P<SymbolType>STK|IDX)(?#
)-(?P<SecurityName>[\.\w \-]{1,16})(?# 
)\s+(?P<TradeType>B|S)(?#
)\s+(?P<Quantity>[-]?\d+)(?#
)\s+(?P<PricePerUnit>\d*(?:\.\d+)?)(?#
)\s+(?P<BrokeragePerUnit>\d*(?:\.\d+)?)(?#
)\s+(?P<NetRatePerUnit>\d*(?:\.\d+)?)(?#
)\s+(?P<NetTotal>[-]?\d+(?:\.\d+)?)(?#
)\s*$\n(?#
)^\s*(?P<SecurityName2>[\S]+).*$(?#
)"""


axisdirect_security_map = {
    "AXIS BANK LIMITED-": "AXISBANK",
    "COAL INDIA LTD-": "COALINDIA",
    "DLF LIMITED-": "DLF",
    "HDFC LTD-INE001A01036": "HDFC",
    "HDFC BANK LTD-": "HDFCBANK",
    "ICICI BANK LTD.-": "ICICIBANK",
    "INDUSIND": "INDUSINDBK",
    "INDUSIND BANK LIMITED-": "INDUSINDBK",
    "INFOSYS LIMITED-": "INFOSYS",
    "INTERGLOBE AVIATION": "INDIGO",
    "KOTAK MAHINDRA BANK": "KOTAK",
    "OIL AND NATURAL GAS": "ONGC",
    "RELIANCE INDUSTRIES": "RELIANCE",
    "SPICEJET LIMITED-": "SPICEJET",
    "STATE BANK OF INDIA-": "SBIN",
    "VODAFONE IDEA LIMITED-": "IDEA",
    "YES BANK LIMITED-": "YESBANK",
    "YES BANK": "YESBANK",
}



def axisdirect_post_process_common(df, metadata=None, action_debug=False):
    df.loc[df['TradeType'] == 'B', 'TradeType'] = 'BUY'
    df.loc[df['TradeType'] == 'S', 'TradeType'] = 'SELL'
    return df

def axisdirect_post_process_eq_df(df, metadata=None, action_debug=False):
    df = axisdirect_post_process_common(df)
    df['SecurityType'] = 'EQ'
    df['SecurityName'] = df['SecurityName'].str.strip()
    return df

def axisdirect_post_process_fno_df(df, metadata=None, action_debug=False):
    df = axisdirect_post_process_common(df)


    df['SecurityName'] = df['SecurityName'] + df['SecurityName2']
    df[['SecurityName', 'ExpirationDate', 'OptionType', 'OptionStrike']] = df['SecurityName'].str.extract(r'(.*)-(.*)-(.*)-(.*)')
    df['SecurityName'] = df['SecurityName'].str.strip()
    df['SecurityType'] = 'OPT'

    # Set the Futures
    df.loc[df['OptionType'].str.contains('FF'), ['SecurityType', 'OptionType', 'OptionStrike']] = ["FUT", "", ""]

    df['ExpirationDate'] = df['ExpirationDate'].apply(lambda x: str(dateutil.parser.parse(x).date()))
    df.drop('SecurityName2', axis=1, inplace=True)

    # print("axisdirect_post_process_fno_df(): ")
    # df_print(df)

    return df


def get_axisdirect_markers():
    return [
        {
            "type": "EQ",
            "regex": axisdirect_eq_regex,
            "post_extraction": axisdirect_post_process_eq_df,
            "suffix": "EQ Trades",
            "security_map": axisdirect_security_map,
            "excel": True
        },
        {
            "type": "FnO",
            "regex": axisdirect_fno_regex,
            "post_extraction": axisdirect_post_process_fno_df,
            "suffix": "FnO Trades",
            "security_map": axisdirect_security_map,
            "excel": True
        }
    ]