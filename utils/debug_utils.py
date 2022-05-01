import inspect
import os
import json

PROJECT_DIR='/Users/neeraj/Projects/Webapps/portfolio-ninja'

INDENT_STR_DEFAULT = "    "

FLAG_ACTIVE_DEFAULT = True
FLAG_FORCE_LOCATION = False


def print_file_function(active=FLAG_ACTIVE_DEFAULT, offset=0, levels=1):
    if not active:
        return

    print(os.getcwd())
    for level in range(levels):
        caller_frame_record = inspect.stack()[level+offset+1]
        frame = caller_frame_record[0]
        info = inspect.getframeinfo(frame)
        file = info.filename
        relative_file_path = os.path.relpath(file, PROJECT_DIR)
        print('[{}:{} {}()]'.format(relative_file_path, info.lineno, info.function))


def debug_log(*args, **kwargs):
    if "active" in kwargs:
        active = kwargs.pop("active")
        if not active:
            return

    if "location" in kwargs:
        location = kwargs.pop("location")
    else:
        location = True

    if "indent_str" in kwargs:
        indent_str = kwargs.pop("indent_str")
    else:
        indent_str = INDENT_STR_DEFAULT

    prefix = ""
    if "indent" in kwargs:
        indent = kwargs.pop("indent")
        prefix = indent_str * indent

    line_start =""
    if "new_line" in kwargs:
        flag_new_line = kwargs.pop("new_line")
        if flag_new_line:
            line_start = "\n"

    offset=0
    if "offset" in kwargs:
        offset = kwargs.pop("offset")

    if location or FLAG_FORCE_LOCATION:
        print_file_function(offset=1+offset)

    print(line_start + prefix, end="")
    print(*args, **kwargs)


def debug_metadata(metadata, *args, **kwargs):
    debug_log("Metadata:", offset=1, **kwargs)
    if 'location' in kwargs:
        kwargs.pop('location')

    debug_log(json.dumps(dict(metadata), default=str, indent=4), *args, location=False, **kwargs)


