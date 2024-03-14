from datetime import datetime
import pytz
from enthost_spider.settings import time_zone


def get_current_time(tz=None):
    if tz is not None:
        tz = pytz.timezone(tz)
    else:
        tz = pytz.timezone(time_zone)
    # TODO need to be fixed
    return datetime.now(tz=tz).replace(tzinfo=None)
