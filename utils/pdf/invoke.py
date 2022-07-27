import subprocess


def subprocess_pdf_to_text(pdf_file_path, text_file_path, password=None, debug=False):
    command = ['pdftotext', '-layout', pdf_file_path, text_file_path]
    if password is not None:
        command.extend(['-upw', password, '-opw', password])

    if debug:
        print("subprocess_pdf_to_text():", " ".join(command))

    subprocess.run(command)


# This extracts the images embedded in a pdf
def subprocess_pdf_extract_images(pdf_file_path, images_root, image_format="png", page_numbers=True, password=None, debug=False):
    command = ['pdfimages']

    if image_format.lower() == "png":
        command.extend(['-png'])

    if page_numbers:
        command.extend(['-p'])

    if password is not None:
        command.extend(['-upw', password, '-opw', password])

    command.extend([pdf_file_path, images_root])

    if debug:
        print("subprocess_pdf_extract_images():", " ".join(command))

    subprocess.run(command)


# This creates images for each page of a pdf
def subprocess_pdf_create_images(pdf_file_path, images_root, image_format="png", password=None, debug=False):
    command = ['pdftoppm']

    if image_format.lower() == "png":
        command.extend(['-png'])

    if password is not None:
        command.extend(['-upw', password, '-opw', password])

    command.extend([pdf_file_path, images_root])

    if debug:
        print("subprocess_pdf_create_images():", " ".join(command))

    subprocess.run(command)


def subprocess_pdf_unlock(pdf_file_path, unlocked_file_path, password, debug=False):
    command = ["qpdf", "--password={}".format(password), '--decrypt', pdf_file_path, unlocked_file_path]

    if debug:
        print(" ".join(command))

    subprocess.run(command)
