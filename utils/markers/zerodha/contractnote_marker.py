import datetime
from datetime import date, timedelta
from utils.date_utils import get_iso_date_from_string


zerodha_eq_regex = r"""(?#
)^(?#
)\s*(?P<Assignment>phy_)?(?P<OrderNum>\d{9,19})(?#
)\s+(?P<OrderTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?P<TradeNum>\d{6,9})(?#
)\s+(?P<TradeTime>\d{2}:\d{2}:\d{2})(?!\s+(\w{1,20}\d{2}\w{3}(FUT|\d{1,8}CE|PE)))(?#
)\s+(?P<SecurityName>[\w\s\/]+)(?#
)\s+(?P<TradeType>B|S)(?#
)\s+(?P<Exchange>\w+)(?#
)\s+(?P<Quantity>[-]?\d+)(?#
)\s+(?P<PricePerUnit>\d+(?:\.\d+)?)(?#
)(?:\s+(?P<BrokeragePerUnit>\d+(?:\.\d+)?))?(?#
)\s+(?P<NetRatePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?P<NetTotal>(?:\d+(?:\.\d+)?)|(?:\(\d+(?:\.\d+)?\)))(?#
)$(?#
)"""

zerodha_fno_regex = r"""(?#
)^(?#
)\s*(?P<OrderNum>\d{16,19})(?#
)\s+(?P<OrderTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?P<TradeNum>\d{7,9})(?#
)\s+(?P<TradeTime>\d{2}:\d{2}:\d{2})(?#
)\s+(?:(?P<SecurityName>\w{1,20})(?P<ExpirationDate>\d{2}\w{3})(?P<DerivativeType>(?:FUT)|(?P<OptionStrike>[\d\.]{1,8})(?P<OptionType>CE|PE)))(?#
)\s+(?P<TradeType>B|S)(?#
)\s+(?P<Exchange>\w+)(?#
)\s+(?P<Quantity>[-]?\d+)(?#
)\s+(?P<PricePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?P<NetRatePerUnit>\d+(?:\.\d+)?)(?#
)(?:\s+(?P<ClosingPricePerUnit>\d+(?:\.\d+)?))?(?#
)\s+(?P<NetTotal>(?:\d+(?:\.\d+)?)|(?:\(\d+(?:\.\d+)?\)))(?#
)$(?#
)"""

zerodha_fnobf_regex = r"""(?#
)^(?#
)\s*(?P<OrderNum>\d{1})(?#
)\s+(?P<TradeNum>\d{1})(?#
)(?:\s+(?P<TradeTime>\d{2}:\d{2}:\d{2}))?(?# optional is not present before 2020-04-07
)\s+(?:(?P<SecurityName>\w{1,20})(?P<ExpirationDate>\d{2}\w{3})(?P<DerivativeType>(?:FUT)|(?P<OptionStrike>[\d\.]{1,8})(?P<OptionType>CE|PE)))(?#
)\s+(?P<TradeType>B|S)(?#
)\s+(?P<Exchange>\w+)(?#
)\s+(?P<Quantity>[-]?\d+)(?#
)\s+(?P<PricePerUnit>\d+(?:\.\d+)?)(?#
)\s+(?P<NetRatePerUnit>\d+(?:\.\d+)?)(?#
)(?:\s+(?P<ClosingPricePerUnit>\d+(?:\.\d+)?))?(?#
)\s+(?P<NetTotal>(?:\d+(?:\.\d+)?)|(?:\(\d+(?:\.\d+)?\)))(?#
)$(?#
)"""


zerodha_charges_minimal_extraction_regex = r"""(?#
)^\s*Equity\s+Futures and Options\s+NET TOTAL\s*$[\n]+(?#
)^(?:.*)\s{10}(?P<GrossAmount>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)(?:[\w\W]*?)(?#
)\s*Net amount[\w\W]+?(?P<NetAmount>[(]?\d+(?:\.\d+)[)]?)$(?#
)"""


zerodha_charges_regex_older = r"""(?#
)^\s*Equity\s+Futures and Options\s+NET TOTAL\s*$[\n]+(?#
)^(?:.*)\s{10}(?P<GrossAmount>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)^(?:.*)\s{10}(?P<Brokerage>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)(?:[\w\W]*?)(?#
)^(?:.*)Exchange.+?\s{10}(?P<ExchangeFee>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)^(?:.*)Clearing.+?(?:\s{10}(?P<ClearingFee>[(]?\d+(?:\.\d+)[)]?))?$[\n]+(?# Three rows foll
)^(?:.*)\s{10}(?P<CGST>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)(?:[\w\W]*?)(?#
)^(?:.*)\s{10}(?P<SGST>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)(?:[\w\W]*?)(?# We are ignoring IGST and UTT4 rows
)^(?:.*)Securities.+?\s{10}(?P<STT>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)^(?:.*)SEBI.+?\s{10}(?P<SEBICharges>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)^\s*Stamp Duty[\w\W]+?(?P<StampDuty>[(]?\d+(?:\.\d+)[)]?)$[\n]+(?#
)\s*Net amount[\w\W]+?(?P<EQAmount>[(]?\d+(?:\.\d+)[)]?)?\s{1,40}(?P<FnOAmount>[(]?\d+(?:\.\d+)[)]?)?\s{1,40}(?P<NetAmount>[(]?\d+(?:\.\d+)[)]?)$(?#
)"""


zerodha_charges_regex=r"""(?#
)^\s*(?P<token1>PAY IN/ PAY OUT OBLIGATION.{50,60})\s{2}(?P<EQGrossAmount>\s{1,30}[(]?\d+(?:\.\d+)[)]?|\s{25})\s{2}(?P<FOGrossAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})\s{2}(?P<GrossAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?||\s{30})$\n(?#
)(?:^.*$\n)*(?#
)^\s*(?P<token2>Net amount receivable by Client / [(]payable by Client[)].{25,33})\s{2}(?P<EQNetAmount>\s{1,30}[(]?\d+(?:\.\d+)[)]?|\s{25})\s{2}(?P<FONetAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})\s{2}(?P<NetAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})$\n(?#
)"""

zerodha_charges_regex_exception_20210228=r"""(?#
)^\s*(?P<token1>(?:PAY IN|Pay in).{20}.{30,50})\s{2}(?P<EQGrossAmount>\s{1,30}[(]?\d+(?:\.\d+)[)]?|\s{25})\s{2}(?P<FOGrossAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})\s{2}(?P<GrossAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?||\s{30})$\n(?#
)(?:^.*$\n)*(?#
)^\s*(?P<token2>Net amount.{43}.{15,23})\s{2}(?P<EQNetAmount>\s{1,30}[(]?\d+(?:\.\d+)[)]?|\s{25})\s{2}(?P<FONetAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})\s{2}(?P<NetAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})$\n(?#
)"""

zerodha_charges_regex_post_20210204=r"""(?#
)^\s*(?P<token1>(?:PAY IN|Pay in).{60}.{30,50})\s{2}(?P<EQGrossAmount>\s{1,30}[(]?\d+(?:\.\d+)[)]?|\s{25})\s{2}(?P<FOGrossAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})\s{2}(?P<GrossAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?||\s{30})$\n(?#
)(?:^.*$\n)*(?#
)^\s*(?P<token2>Net amount.{83}.{15,23})\s{2}(?P<EQNetAmount>\s{1,30}[(]?\d+(?:\.\d+)[)]?|\s{25})\s{2}(?P<FONetAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})\s{2}(?P<NetAmount>\s{1,40}[(]?\d+(?:\.\d+)[)]?|\s{30})$\n(?#
)"""


# {0:Monday,... , 6:Sunday}

def all_thursdays_in_month(year, month):
    # Find the number of days to first thursday
    thursday = 3
    dt = date(year, month, 1)

    days = thursday - dt.weekday()
    if days < 0:
        days += 7

    # First Sunday of the given year
    dt += timedelta(days)
    while dt.year == year and dt.month == month:
        yield dt
        dt += timedelta(days=7)

def all_sundays_in_year(year):
    # January 1st of the given year
    dt = date(year, 1, 1)
    # First Sunday of the given year
    dt += timedelta(days=6 - dt.weekday())
    while dt.year == year:
        yield dt
        dt += timedelta(days=7)


def get_last_thursday_of_month(year, month):
    return list(all_thursdays_in_month(year, month))[-1]

def get_last_thursday_of_month_by_date(date):
    return list(all_thursdays_in_month(date.year, date.month))[-1]

def get_last_thursday_by_date_str(date_str):
    return get_last_thursday_of_month_by_date(get_iso_date_from_string(date_str, "%y%b"))


def zerodha_post_process_common(df, metadata=None, action_debug=False):
    df.loc[df['TradeType'] == 'B', 'TradeType'] = 'BUY'
    df.loc[df['TradeType'] == 'S', 'TradeType'] = 'SELL'
    return df


def zerodha_post_process_eq_df(df, metadata=None, action_debug=False):
    df = zerodha_post_process_common(df)
    df['SecurityType'] = "EQ"

    if "Assignment" in df.columns:
        df['Quantity'] = df['Quantity'].astype(int)
        df['PricePerUnit'] = df['PricePerUnit'].astype(float)
        df.loc[df.Assignment.notna(), 'NetTotal'] = df['Quantity'] * df['PricePerUnit']
        df.loc[df.Assignment.notna(), 'BrokeragePerUnit'] = df['PricePerUnit'] * .0025

    return df


def zerodha_post_process_fno_df(df, metadata=None, action_debug=False):
    df = zerodha_post_process_common(df)

    # Any dates in the table should be converted to ISO format
    df['ExpirationDate'] = df['ExpirationDate'].apply(lambda x: str(get_last_thursday_by_date_str(x)))

    # Extract columns from column DerivativeType
    df.loc[df['DerivativeType'] != 'FUT', 'DerivativeType'] = 'OPT'
    df.rename({'DerivativeType': 'SecurityType'}, axis=1, inplace=True)

    return df


def zerodha_post_process_fnobf_df(df, metadata=None, action_debug=False):
    df = zerodha_post_process_fno_df(df)
    return df


def zerodha_post_process_charges_df(df, metadata=None, action_debug=False):
    return df


def get_zerodha_markers():
    return [
        {
            "regex": zerodha_eq_regex,
            "type": "EQ",
            "post_extraction": zerodha_post_process_eq_df,
            "suffix": "EQ Trades",
            "excel": True
        },
        {
            "regex": zerodha_fno_regex,
            "type": "FnO",
            "post_extraction": zerodha_post_process_fno_df,
            "suffix": "FnO Trades",
            "excel": True
        },
        {
            "regex": zerodha_fnobf_regex,
            "type": "FnOBF",
            "post_extraction": zerodha_post_process_fnobf_df,
            "suffix": "FnOBF",
            "excel": True
        },
        {
            "regex": zerodha_charges_regex_post_20210204,
            "bounded": [
                {
                    "max_date": "2021-02-03",
                    "regex": [zerodha_charges_regex, zerodha_charges_regex_exception_20210228],
                },
                {
                    "max_date": "2023-03-31",
                    "regex": zerodha_charges_regex_post_20210204
                }
            ],
            "type": "Expenses",
            "post_extraction": zerodha_post_process_charges_df,
            "suffix": "Charges",
            "excel": True
        }
    ]


financial_year_range_map = {
    'FY201718': {
        'lower': datetime.date(2017, 3, 31),
        'upper': datetime.date(2028, 4, 1)
    },
    'FY201819': {
        'lower': datetime.date(2018, 3, 31),
        'upper': datetime.date(2019, 4, 1)
    },
    'FY201920': {
        'lower': datetime.date(2019, 3, 31),
        'upper': datetime.date(2020, 4, 1)
    },
    'FY202021': {
        'lower': datetime.date(2020, 3, 31),
        'upper': datetime.date(2021, 4, 1)
    },
    'FY202122': {
        'lower': datetime.date(2021, 3, 31),
        'upper': datetime.date(2022, 4, 1)
    }
}

def get_dates_range(financial_year):
    if financial_year not in financial_year_range_map.keys():
        raise Exception

    return (financial_year_range_map[financial_year]['lower'], financial_year_range_map[financial_year]['upper'])

def get_date_filter(financial_year):
    lower_date, upper_date = get_dates_range(financial_year)

    # Kept for testing purpose
    single_date = {"date__eq": datetime.date(2019, 4, 23)}
    date_range_custom = {
        "date__gt": datetime.date(2020, 10, 3),
        "date__lt": datetime.date(2020, 11, 2)
    }

    date_range = {
        "date__gt": lower_date,
        "date__lt": upper_date
    }

    flag_date_range = False
    filter_date = date_range if flag_date_range else single_date
    return filter_date

def get_zerodha_extraction(financial_year, input_folder, output_folder):
    account_markers = get_zerodha_markers(output_folder)
    filter_date = get_date_filter(financial_year)

    return {
        "Type": "ProcessFolder",
        "Description": "Extract Trades from Contract Notes and store them in Excel",
        "Active": True,
        "Debug": True,

        "Input": {
            "Type": "Folder",
            "Parameters": {
                "Path": input_folder,
                "Filter": dict({"extension": ".pdf"}, **filter_date),
                "Sort": "Name"
            }
        },
        "Actions": [
            {
                "name": "ExtractTableRegex",
                "active": 1,
                "debug": False,
                "parameters": {
                    "noMatchOk": False,
                    "markers": account_markers,
                    "contractnote": {
                        "active": True,
                        "subfolder": input_folder,
                        "filename": "{}_Contract_Note_(TradeDate).xlsx".format(account_name),
                    }
                }
            }
        ]
    }