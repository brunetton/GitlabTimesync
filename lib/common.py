import datetime
import sys
import logging

import arrow
from arrow.parser import ParserMatchError

log = logging.getLogger(__name__)


def print_(string):
    '''Print the string without end line break'''
    print(string),  # Here the end-line coma is intended
    sys.stdout.flush()


# -*- Parsing args functions -*-


def parse_date(datestr, date_formats):
    '''Try all dates formats defined in date_formats array and returns an Arrow object representing that date.
    If format doesn't containt year, default assign current year to returned date (instead of 1900).
    Returns: Arrow object or None
    '''
    assert datestr
    assert date_formats and isinstance(date_formats, list), date_formats
    for date_format in date_formats:
        date_format = date_format.strip()
        try:
            date = arrow.get(datestr, date_format)
            if date_format.find('Y') == -1:
                # date format doesn't containts year, let's assume it's current year
                current_year = datetime.date.today().year
                return date.replace(year=current_year)
            return date
        except ParserMatchError:
            pass
    return None


def quit_with_parse_date_error(datestr, date_formats):
    print("Error while parsing date '{}'.\nAccepted formats defined in config file are: {}.".format(datestr, date_formats))
    sys.exit(-1)


def parse_date_or_days_ahead(datestr, config, quit_if_none=False):
    '''Returns a arrow date corresponding to given date, or days ahead number.
    quit_if_none: quit program if no date parsed

    parse_date_or_days_ahead('4/10/2014') should return corresponding date, if that format is defined in config file
    parse_date_or_days_ahead('1') should return the date of yesterday
    '''
    if datestr.isdigit():
        # It's a number, corresponding to some days ago from today. Return that date
        return arrow.now().shift(days=int(datestr))
    # Try to find a formatted date
    date_formats = list(map(str.strip, config.get('default', 'date_formats').split(',')))
    date = parse_date(datestr, date_formats)
    if date:
        return date
    if quit_if_none:
        quit_with_parse_date_error(datestr, date_formats)
    return None


def parse_dates_in_args(args, config):
    '''Returns from_date, to_date or for_date Arrow dates from given args array
    nb: if from_date is not None; to_date could be None or not.
    '''
    assert args
    from_date = to_date = for_date = None
    if args['from']:
        from_date = parse_date_or_days_ahead(args['<start>'], config, quit_if_none=True)
    if args['to']:
        to_date = parse_date_or_days_ahead(args['<stop>'], config)
    if args['<date>']:
        for_date = parse_date_or_days_ahead(args['<date>'], config, quit_if_none=True)
    return from_date, to_date, for_date
