import os
import shutil


def get_base_name(file_path):
    if file_path is None or not isinstance(file_path, str):
        return None

    file_name = os.path.basename(file_path)
    parts = os.path.splitext(file_name)
    return parts[0]


def get_extn(file_path):
    if file_path is None or not isinstance(file_path, str):
        return None

    file_name = os.path.basename(file_path)
    parts = os.path.splitext(file_name)

    if (len(parts) > 1):
        extn = parts[1]
    else:
        extn = ""
    
    return extn


def get_extn_no_dot(file_path):
    return get_extn(file_path)[1:]

def replace_extn(file_path, extn, suffix=None, underscore="True"):
    dir_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    
    parts = os.path.splitext(file_name)
    
    base_name = parts[0]
    if suffix is not None:
        joiner = "_" if underscore else ""
        base_name = joiner.join([base_name, suffix])
           
    if (len(parts) > 1):
        joiner = "" if extn[0] == '.' else "."
        # if (extn[0] == '.'):
        #     joiner = ""
        # else:
        #     joiner = "."
        
        file_name = joiner.join([base_name, extn])    
    else:
        file_name = base_name
    
    return os.path.join(dir_path, file_name)


def get_relative_path(path, start_path):
    return os.path.relpath(path, start=start_path)


def add_suffix(file_path, suffix, underscore="True"):
    extn = get_extn(file_path)
    return replace_extn(file_path, extn, suffix=suffix, underscore=underscore)


def get_path(file_path):
    return os.path.dirname(file_path)


def get_file(file_path):
    return os.path.basename(file_path)


def get_text_file_extn():
    return ".txt"


def get_excel_file_extn():
    return ".xlsx"


def get_json_file_extn():
    return ".json"


def is_pdf(file_path):
    return get_extn(file_path).lower() == ".pdf"

def is_png(file_path):
    return get_extn(file_path).lower() == ".png"

def is_jpeg(file_path):
    extn = get_extn(file_path).lower()
    return extn == ".jpeg" or extn == ".jpg"

def is_txt(file_path):
    l_extn = get_extn(file_path).lower()
    return  l_extn == ".txt" or l_extn == ".text"

def is_csv(file_path):
    l_extn = get_extn(file_path).lower()
    return  l_extn == ".csv"

def is_xlsx(file_path):
    l_extn = get_extn(file_path).lower()
    return  l_extn == ".xlsx"


def copy_file(src, dst):
    shutil.copy(src, dst)

def move_file(src, dst):
    shutil.move(src, dst)
