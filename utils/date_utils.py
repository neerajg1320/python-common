import re
from datetime import datetime, timedelta


def get_datetime_from_string(input_str, regex=None):
    if regex is None:
        regex = r"(?P<date>\d{4}-\d{2}-\d{2})"

    p = re.compile(regex)
    m = p.findall(input_str)

    date_str = None
    if m is not None and len(m) > 0:
        date_str = m[0]

    ts = None
    if date_str is not None:
        ts = datetime.strptime(date_str, "%Y-%m-%d")

    return ts


def get_date_from_string(input_str, regex=None):
    ts = get_datetime_from_string(input_str, regex=regex)
    if ts is not None:
        return ts.date()

    return None


def get_iso_date_from_string(input_str, format="%Y-%m-%d"):
    return datetime.strptime(input_str, format)


def get_iso_string_from_date(input_date, format="%Y-%m-%d"):
    return datetime.strftime(input_date, format)


def subtract_days(date, num_days):
    return date - timedelta(days=num_days)


def add_days(date, num_days):
    return date + timedelta(days=num_days)
