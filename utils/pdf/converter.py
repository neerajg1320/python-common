import pdftotext


def get_pdf_text(input_file_path):
    text = None
    try:
        with open(input_file_path, "rb") as f:
            pages = pdftotext.PDF(f)
        text = "\n\n".join(pages)
    except pdftotext.Error as e:
        print(e)

    return text


def pdf_to_text(input_file_path, output_file_path):
    text = get_pdf_text(input_file_path)

    if text is not None:
        with open(output_file_path, "w") as f:
          f.write(text)
    else:
        print(input_file_path + ": PDF read error")
