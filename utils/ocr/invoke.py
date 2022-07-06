import subprocess


def subprocess_image_ocr(image_file_path, text_file_path, debug=True):
    command = ['tesseract', image_file_path, text_file_path, "-c", "preserve_interword_spaces=1"]


    if debug:
        print("subprocess_image_ocr():", " ".join(command))

    subprocess.run(command)
