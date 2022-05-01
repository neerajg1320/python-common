import pytz
import datetime


# https://www.kite.com/python/answers/how-to-set-the-timezone-of-a-datetime-in-python#:~:text=Use%20pytz.,the%20timezone%20of%20a%20datetime
def add_time_zone_utc(date):
    # print("get_date_time(): type(date)={} date={}".format(type(date), date))
    timezone = pytz.timezone("UTC")
    date = timezone.localize(date)
    # print("get_date_time(): type(date)={} date={}".format(type(date), date))

    return date


# Need to watchout for timezone
def get_current_time():
    return datetime.datetime.now().replace(tzinfo=pytz.utc)


def get_datetime(year, month, day, hours=0, minutes=0, seconds=0, ms=0):
    return add_time_zone_utc(datetime.datetime(year, month, day, hours, minutes))


def get_datetime_from_string(datetime_str, format="%Y-%m-%d"):
    return add_time_zone_utc(datetime.datetime.strptime(datetime_str, format))


def get_isoformat_date_str_from_datetime(datetime):
    return datetime.strftime("%Y-%m-%d")
