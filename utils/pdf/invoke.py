import subprocess


def pdf_to_text_subprocess(pdf_file_path, text_file_path, password=None, debug=False):
    command = ['pdftotext', '-layout', pdf_file_path, text_file_path]
    if password is not None:
        command.extend(['-upw', password, '-opw', password])

    if debug:
        print(" ".join(command))

    subprocess.run(command)


def pdf_unlock_subprocess(pdf_file_path, unlocked_file_path, password, debug=False):
    command = ["qpdf", "--password={}".format(password), '--decrypt', pdf_file_path, unlocked_file_path]

    if debug:
        print(" ".join(command))

    subprocess.run(command)
