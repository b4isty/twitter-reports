from datetime import datetime


def custom_time_now():
    """
    Custom time function to get
    time diff in second using it
    """
    fmt = "%H%M%S"
    return datetime.strptime(datetime.strftime(datetime.now(), fmt), fmt)