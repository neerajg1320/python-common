import subprocess


def subprocess_image_ocr(image_file_path, text_file_path, debug=True):
    # command = ['tesseract', "--psm", "6", "-c", "preserve_interword_spaces=1", image_file_path, text_file_path]
    command = ['tesseract', "--psm", "6", image_file_path, text_file_path]
    # command = ['tesseract', image_file_path, text_file_path]

    if debug:
        print("subprocess_image_ocr():", " ".join(command))

    subprocess.run(command)
