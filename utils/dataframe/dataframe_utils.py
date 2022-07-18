import os.path
import re
import pandas as pd
import json
import logging
from utils.regex_utils import check_compile_regex
from utils.debug_utils import print_file_function


logger = logging.getLogger(__name__)


def is_dataframe(var):
    return isinstance(var, pd.DataFrame)


def df_new_dataframe():
    return pd.DataFrame()


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

def df_print(df, dtypes=False, index=False, shape=False, new_line=True, gui=False, active=True, location=True, columns=False):
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

        if columns:
            print(df.columns)


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


def df_to_oriented_json(df):
    return json.loads(df.to_json(orient="table"))


def df_from_oriented_json(json_data):
    return pd.read_json(json.dumps(json_data), orient='table')


# https://stackoverflow.com/questions/49519696/getting-attributeerror-workbook-object-has-no-attribute-add-worksheet-whil
def df_append_excel(df, file_path, sheet_name, **kwargs):
    """
    Append a DataFrame [df] to existing Excel file [filename]
    into [sheet_name] Sheet.
    If [filename] doesn't exist, then this function will create it.

    Parameters:
      filename : File path or existing ExcelWriter
                 (Example: '/path/to/file.xlsx')
      df : dataframe to save to workbook
      sheet_name : Name of sheet which will contain DataFrame.
                   (default: 'Sheet1')
      startrow : upper left cell row to dump data frame.
                 Per default (startrow=None) calculate the last row
                 in the existing DF and write to the next row...
      truncate_sheet : truncate (remove and recreate) [sheet_name]
                       before writing DataFrame to Excel file
      to_excel_kwargs : arguments which will be passed to `DataFrame.to_excel()`
                        [can be dictionary]

    Returns: None
    """
    from openpyxl import load_workbook

    # ignore [engine] parameter if it was passed
    if 'engine' in kwargs:
        kwargs.pop('engine')
    startrow = kwargs.pop('startrow', None)
    truncate_sheet = kwargs.pop('truncate_sheet', None)

    if 'index' not in kwargs:
        kwargs['index'] = False

    file_exists = os.path.exists(file_path)
    if file_exists:
        book = load_workbook(file_path)

    # This will create a file of size zero
    writer = pd.ExcelWriter(file_path,
                            engine='openpyxl',
                            datetime_format='yyyy-mm-dd',
                            date_format='yyyy-mm-dd')

    if file_exists:
        writer.book = book
        # logger.info("Existing sheetnames={}".format(writer.book.sheetnames))

    # get the last row in the existing Excel sheet
    # if it was not specified explicitly
    if startrow is None and sheet_name in writer.book.sheetnames:
        startrow = writer.book[sheet_name].max_row

    # truncate sheet
    if truncate_sheet and sheet_name in writer.book.sheetnames:
        # index of [sheet_name] sheet
        idx = writer.book.sheetnames.index(sheet_name)
        # remove [sheet_name]
        writer.book.remove(writer.book.worksheets[idx])
        # create an empty sheet [sheet_name] using old index
        writer.book.create_sheet(sheet_name, idx)

    # copy existing sheets
    writer.sheets = {ws.title:ws for ws in writer.book.worksheets}

    if startrow is None:
        startrow = 0

    # write out the new sheet
    df.to_excel(writer, sheet_name=sheet_name, startrow=startrow, **kwargs)

    # save the workbook
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

def df_filter_by_row_signature(df, signature, header_signature=None, debug=False):
    frame = df_signature(df)

    if debug:
        print("process_frame_with_signature(): Show signature")
        df_print(frame.apply(lambda row: get_signature(row), axis=1))

    boolean_frame = frame.apply(lambda row: filter_by_signature(row, signature, header_signature=header_signature),
                                axis=1)
    return df[boolean_frame]


def df_signature(df):
    frame = df.applymap(type)
    frame = frame.applymap(lambda x: x.__name__)
    return frame


def df_is_empty(df):
    return df.empty
