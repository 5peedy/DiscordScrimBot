import datetime


def get_today():
    today = datetime.date.today()
    return today


def get_tomorrow():
    today = datetime.date.today()
    return today + datetime.timedelta(days=1)
