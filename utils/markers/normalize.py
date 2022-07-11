import pandas as pd
import numpy as np
from utils.dataframe.dataframe_utils import df_print


# Zerodha Specific: currently
def clean_security_name(x):
    if not isinstance(x, str):
        return x

    if '/' in x:
        x = x.split('/')[0]

    return x.strip()


def clean_number(x):
    if not isinstance(x, str):
        return x

    x = x.strip()

    if len(x) < 1:
        return x

    negative = False

    if x[0] == '(' and x[-1] == ')':
        negative = True

    x = x.replace("(","").replace(")","").replace(",","")

    if negative:
        x = "".join(["-", x])
    return x


def normalize_trades(df, marker_type, flagConsolidate=True):
    if "SecurityName" not in df.columns:
        raise Exception

    unknown_trades_df = df[(df['TradeType'].str.upper() != "BUY") & (df['TradeType'].str.upper() != "SELL")]
    if unknown_trades_df.shape[0] > 0:
        df_print(unknown_trades_df)
        raise Exception

    # Zerodha: needs to be moved to broker specific code
    df['SecurityName'] = df['SecurityName'].apply(clean_security_name)

    # Delete the Time columns: 'OrderTime' and 'TradeTime'
    for column in df.columns:
        if isinstance(column, str):
            if 'Time' in column:
                df = df.drop(column, axis=1)

    df['Quantity'] = df['Quantity'].apply(clean_number)
    df['NetTotal'] = df['NetTotal'].apply(clean_number)

    # raise: Non-numeric will raise an exception
    # coerce: Non-numeric objects will turn into NaN
    # ignore: Non-numeric will be returned as is
    # The blank strings will become np.float64 with value np.nan
    df = df.apply(pd.to_numeric, errors='ignore')
    df['OrderNum'] = df['OrderNum'].astype(str)

    if df['Quantity'].dtype != np.int64:
        print(df['Quantity'].dtype)
        raise Exception
    if df['NetTotal'].dtype != np.float64:
        print(df['NetTotal'].dtype)
        raise Exception

    if 'BrokeragePerUnit' not in df.columns:
        df['BrokeragePerUnit'] = 0
    else:
        # Sometimes Brokerage is nan
        df['BrokeragePerUnit'] = df['BrokeragePerUnit'].replace(np.nan, 0)

    if not df.empty and flagConsolidate:
        if marker_type != "FnOBF":
            # Using agg function
            # We have to watch out for a case where the aggregate brokerage is different than desired
            column_dict = {
                'SecurityName': 'first',
                'SecurityType': 'first',
                'TradeType': 'first',
                'Quantity': 'sum',
                'BrokeragePerUnit': 'mean',
                'PricePerUnit': 'mean',
                'NetTotal': 'sum'
            }

            derivatives_columns_dict = {
                    "ExpirationDate": "first",
                    "OptionStrike": "first",
                    "OptionType": "first",
                }

            if "ClosingPricePerUnit" in df.columns:
                derivatives_columns_dict.update({"ClosingPricePerUnit": "mean"})

            if "ExpirationDate" in df.columns:
                column_dict.update(derivatives_columns_dict)

            df = df.groupby(['OrderNum']) \
                .agg(column_dict)

            # We turn all into positive
            df['Quantity'] = df['Quantity'].abs()
            df['BrokeragePerUnit'] = df['BrokeragePerUnit'].abs()
            df['NetTotal'] = df['NetTotal'].abs()

            # We are using rates as positives only
            df['NetRatePerUnit'] = df['NetTotal'] / df['Quantity']

            # We use (-) negative for sell trades
            df.loc[df['TradeType'] == 'SELL', 'NetTotal'] = -df['NetTotal']

            # Here we have to use the fact that per order brokerage is fixed for this account
            df['Brokerage'] = df['Quantity'] * df['BrokeragePerUnit']

            df['GrossTotal'] = df['NetTotal'] - df['Brokerage']
            df['GrossRatePerUnit'] = df['GrossTotal'].abs() / df['Quantity']

            # Change the Quantity to negative if it is a sell transaction i.e. TradeType=='SELL'
            df.loc[df['TradeType'] == 'SELL', 'Quantity'] = -df['Quantity']

            # Here we rearrange the columns
            column_list = ['SecurityName', 'SecurityType']

            if "ExpirationDate" in df.columns:
                column_list.extend(list(derivatives_columns_dict.keys()))

            df['OrderNum'] = df.index
            common_column_list = ['OrderNum', 'TradeType', 'Quantity', 'GrossTotal', 'GrossRatePerUnit',
                                  'Brokerage','BrokeragePerUnit', 'NetTotal', 'NetRatePerUnit']
            column_list.extend(common_column_list)

            df = df[column_list]
        else:
            df['Quantity'] = df['Quantity'].abs()
            df.loc[df['TradeType'] == 'SELL', 'Quantity'] = -df['Quantity']

            # Using agg function
            # We have to watch out for a case where the aggregate brokerage is different than desired
            # We group by SecurityName because OrderNum is 0 for FnOBF
            #
            df = df.groupby(['SecurityName']) \
                .agg({
                'SecurityName': 'first',
                "ExpirationDate": "first",
                "OptionStrike": "first",
                "OptionType": "first",
                'SecurityType': 'first',
                'TradeType': 'first',
                'Quantity': 'sum',
                'NetRatePerUnit': 'mean',
                'ClosingPricePerUnit': 'mean',
                'NetTotal': 'sum'
            })
            df = df[['SecurityName', 'SecurityType', 'ExpirationDate', 'OptionStrike', 'OptionType', 'TradeType', 'Quantity', 'NetRatePerUnit', 'ClosingPricePerUnit', 'NetTotal']]

        if "ClosingPricePerUnit" in df.columns:
            df['MTM'] = (df['NetRatePerUnit'] - df['ClosingPricePerUnit']) * df['Quantity']

        if 'MTM' in df.columns:
            df['C_NetTotal'] = df['MTM']
            df.loc[df['C_NetTotal'].isnull(), 'C_NetTotal'] = df['NetTotal']
        else:
            df['C_NetTotal'] = df['NetTotal']

    return df


# This has been kept here for two reasons
# If we want to change the logic to convert to numeric then we need to change at only one place
# This limits the import of pandas to this file
def convert_to_numeric(df, errors='coerce'):
    return df.apply(pd.to_numeric, errors=errors)


def normalize_expenses(df):
    df = df.applymap(clean_number)
    df = df.apply(pd.to_numeric, errors='ignore')

    # print("normalize_expenses(): df.columns={}".format(list(df.columns)))
    df.reset_index(drop=True, inplace=True)

    return df
