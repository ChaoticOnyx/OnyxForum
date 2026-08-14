import datetime


MOSCOW_TIMEZONE = datetime.timezone(datetime.timedelta(hours=3), name="МСК")


def format_moscow_datetime(value):
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(MOSCOW_TIMEZONE).strftime("%d.%m.%Y, %H:%M по МСК")
