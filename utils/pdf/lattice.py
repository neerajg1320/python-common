import camelot


def pdf_to_tables(file_path, pages='1', file_password=None, debug=False):
    tables = camelot.read_pdf(file_path, pages=pages)
    df_list = []
    for table in tables:
        df_list.append(table.df)

    return df_list
