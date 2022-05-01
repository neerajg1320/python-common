import re
import pandas as pd
from utils.regex_utils import check_compile_regex
from utils.debug_utils import print_file_function


def is_dataframe(var):
    return isinstance(var, pd.DataFrame)


def create_df_from_text_using_regex(regex_text, input_file_text, flags=None):
    # error = None
    # print("Regex Text: ", regex_text)
    # print("Error: ", error)

    p, error = check_compile_regex(regex_text, flags=flags)

    if error:
        print("Regex has errors: ", error)
        return None

    s = pd.Series(input_file_text)
    df = pd.DataFrame()
    try:
        df = s.str.extractall(regex_text , re.MULTILINE)
    except ValueError as e:
        print(e)

    return df


FLAG_ACTIVE_DEFAULT = True
FLAG_FORCE_LOCATION = False

def df_print(df, dtypes=False, index=False, shape=False, new_line=True, gui=False, active=True, location=True):
    if not active:
        return

    # https://stackoverflow.com/questions/6810999/how-to-determine-file-function-and-line-number

    # Use this as a decorator
    if location or FLAG_FORCE_LOCATION:
        print_file_function(offset=1, levels=4)

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.float_format', lambda x: '%.2f' % x)

    if gui:
        # gui = show(df, settings={'block': True})
        print("pandas_gui not used")
    else:
        if new_line:
            print()

        print(df)

        if index:
            print(df.index)

        if shape:
            print(df.shape)

        if dtypes:
            print(df.dtypes)


def df_read_excel(*args, **kwargs):
    return pd.read_excel(*args, **kwargs)


def df_read_csv(*args, **kwargs):
    return pd.read_csv(*args, **kwargs)


# https://xlsxwriter.readthedocs.io/example_pandas_datetime.html
def df_write_excel(df, filepath, *args, **kwargs):
    if 'index' not in kwargs:
        kwargs['index'] = False

    writer = pd.ExcelWriter(filepath,
                            engine='xlsxwriter',
                            datetime_format='yyyy-mm-dd',
                            date_format='yyyy-mm-dd')

    df.to_excel(writer, *args, **kwargs)
    writer.save()


def dflist_write_excel(dflist, filepath, *args, **kwargs):
    if 'index' not in kwargs:
        kwargs['index'] = False

    writer = pd.ExcelWriter(filepath,
                            engine='xlsxwriter',
                            datetime_format='yyyy-mm-dd',
                            date_format='yyyy-mm-dd')

    for dfentry in dflist:
        df = dfentry['dataframe']
        suffix = dfentry['suffix']
        # print('{} df.dtypes:'.format(suffix), df.dtypes)
        # df_print(df)
        if suffix is None or suffix == "":
            suffix = "Sheet1"
            print('dflist_write_excel: no sheetname provided, using default {}'.format(suffix))
        df.to_excel(writer, sheet_name=suffix, *args, **kwargs)

    writer.save()


# https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
# Usage:
# with SupressSettingWithCopyWarning():
#     code that produces warning
#
class SupressSettingWithCopyWarning:
    def __enter__(self):
        pd.options.mode.chained_assignment = None

    def __exit__(self, *args):
        pd.options.mode.chained_assignment = 'warn'


def get_signature(row):
    arr = []
    for cell in row:
        arr.append(cell[0])
    return ''.join(arr)


def filter_by_signature(row, signature, header_signature=None):
    row_signature = get_signature(row)

    if row_signature == signature:
        return True

    if header_signature is not None and row_signature == header_signature:
        return True

    return False
