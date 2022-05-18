from utils.date_utils import get_date_from_string
from utils.dataframe_utils import create_df_from_text_using_regex, \
    df_print, SupressSettingWithCopyWarning, filter_by_signature, get_signature
from .normalize import normalize_trades, normalize_expenses
from utils.markers.zerodha.contractnote_marker import get_zerodha_markers
from utils.markers.axisdirect.contractnote_marker import get_axisdirect_markers
from utils.markers.indiainfoline.contractnote_marker import get_indiainfoline_markers


def get_date_from_filepath(file_path):
    return get_date_from_string(file_path)

# TBD: We need to update this function
def get_markers(account, document_type):
    # We need to fix this part.
    # Need to move these to pipeline processing
    if "zerodha" in account.lower() and document_type == "ContractNote":
        return get_zerodha_markers()
    elif "axisdirect" in account.lower() and document_type == "ContractNote":
        return get_axisdirect_markers()
    elif "indiainfoline" in account.lower() and document_type == "ContractNote":
        return get_indiainfoline_markers()
    else:
        # raise Exception("Marker for ({}, {}) not supported".format(account, document_type))
        return None


def process_text_with_regex(input_text, regex_text):
    return create_df_from_text_using_regex(regex_text, input_text)

# markers is an array of regex followed with post processing functions
def process_text_with_markers(input_text, markers, meta_data, debug=True):
    file_date = meta_data['file_date']
    if debug:
        print("process_text_with_markers(): file_date={}".format(file_date))

    flagAllTrades = False
    dfs = []

    for marker in markers:
        marker_type = marker['type']

        regexes = None
        if 'bounded' in marker:
            bounded = marker['bounded']

            for bound in bounded:
                max_date = bound['max_date']
                if file_date is not None and file_date <= get_date_from_string(max_date):
                    regexes = bound['regex']
                    if debug:
                        print("process_text_with_markers(): regex selected bounded['max_date']={}".format(max_date))
                    break

        if regexes is None:
            regexes = marker['regex']

        regexlist = [regexes] if not isinstance(regexes, list) else regexes

        ri = 0
        for regex in regexlist:
            df = process_text_with_regex(input_text, regex)

            if not df.empty:
                # call the post processing function if it exists
                post_process = marker.get('post_extraction', None)
                if post_process is not None:
                    df = marker['post_extraction'](df)
                    if flagAllTrades:
                        dfs.append({'suffix': "_".join([marker_type, "All"]), 'dataframe': df})

                    if marker_type == "EQ" or marker_type == "FnO" or marker_type == "FnOBF":
                        df = normalize_trades(df, marker_type)
                    elif marker_type == "Expenses":
                        df = normalize_expenses(df)
                    else:
                        print('marker_type {} not supported'.format(marker_type))

                    df['Date'] = meta_data['file_date']

                    security_map = marker.get('security_map', None)
                    if security_map is not None:
                        print("process_text_with_markers(): applying security_map")
                        df.replace({'SecurityName': security_map}, inplace=True)

                # Here we will save the file with suffix
                # print("process_text_with_markers(): Appending df: {}".format(marker['suffix']))
                dfs.append({'suffix': marker['suffix'], 'dataframe': df})
                break
            else:
                print('Marker {}[{}] did not match'.format(marker_type, ri))
                pass

            ri += 1

    return dfs
