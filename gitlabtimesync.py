#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import os
import re
import sqlite3
import sys
from configparser import RawConfigParser
from pprint import pformat
import logging
from collections import defaultdict

import arrow
from docopt import docopt  # http://docopt.org/
from requests import ConnectionError

from lib import common, gitlab
from lib.common import print_

log = logging.getLogger(__name__)

CONFIG_FILE = 'gitlabtimesync.config'
DB_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH:mm:ss'

DOC = '''
Gitlab / Hamster times entries synchronization

Usage:
    {self_name} from <start> [(to <stop>)] [options]
    {self_name} <date> [options]
    {self_name} -h | --help

Options:
    -a --auto             Do not ask for manual validation for each day, sync all days in given interval
    -n --no-date-confirm  Do not ask for manual dates interval confirmation at begining
    --debug               Display debug messages

Note: start, stop and date could be :
    - a date: ("12/10", "12/10/15", ...)
      -> check for config file to change dates formats
    - a number of days ago: ("3" means 3 days ago, "1" means yesterday, ...)
      -> 0 means today
'''


def getTimeEntries(date, config):
    '''Reads Sqlite Hamster DB file and return an array of explicit associative array for times entries for given date,
    filtering out entries that do not match issue_id_regexp defined in config file
    Returns:
        - activities_array:
            array of dicts with 'description', 'label', 'issue_id', 'duration', 'comment', 'activity_id' keys
        - times_by_issue_id: sum times indexed by activity id
    '''

    def fetchFromDatabase(db_filename, date):
        '''Fetch data from an SQLITE3 database
        Returns an iterable object with SELECT result'''
        _date = "%{}%".format(date.format('YYYY-MM-DD'))
        connection = sqlite3.connect(os.path.expanduser(db_filename))
        if args['--debug']:
            connection.set_trace_callback(print)
        dbCursor = connection.cursor()
        dbCursor.execute("""SELECT
            activities.name,facts.start_time,facts.end_time,facts.description,categories.name
            FROM activities
            JOIN facts ON activities.id = facts.activity_id
            LEFT JOIN categories ON activities.category_id = categories.id
            WHERE facts.start_time LIKE ?
            ORDER BY start_time""", (_date,)
                         )
        return dbCursor

    db_filename = config.get('default', 'db')
    time_entries = fetchFromDatabase(db_filename, date)
    activities = []
    times_by_issue_id = defaultdict(float)
    total_duration = 0
    log.debug("Parsing entries from database ...")
    for time_entry in time_entries:
        # Try to find Gitlab issue IDs from label using regexp defined in config file
        label = time_entry[0]
        log.debug("-> {!r}".format(label))
        match = re.match(config.get('default', 'issue_id_regexp'), label)
        if not match:
            print('** Warning: ignoring entry "{}" : not able to find issue ID\n'.format(label))
            continue
        issue_id = match.group(1)
        if not time_entry[2]:
            print(('** Warning: ignoring "{}": Not completed yet\n'.format(label)))
            continue
        duration = (arrow.get(time_entry[2], DB_TIMESTAMP_FORMAT) -
                    arrow.get(time_entry[1], DB_TIMESTAMP_FORMAT)).seconds / 3600.
        assert duration > 0, "Duration for entry {} is not >0: {}".format(label, duration)
        total_duration += duration
        times_by_issue_id[issue_id] += duration
        duration = round(duration, 2)
        comment = time_entry[3]
        print("* [{duration}h #{id}]: {label}".format(
            duration=duration, id=issue_id, label=label
        ))
        if comment is not None:
            print("  {}".format(comment))
        activities.append({
            'description': label,
            'label': label,
            'issue_id': issue_id,
            'duration': duration,
            'comment': comment,
        })
    # Display sums
    total_duration = round(total_duration, 2)
    if total_duration > 0:
        # Display times_by_issue_id and round durations
        print("\nData to send:")
        for issue_id, duration in times_by_issue_id.items():
            duration = round(duration, 2)
            times_by_issue_id[issue_id] = duration
            print("  - #{}: {}h".format(issue_id, duration))
        print("\nTotal : {}h".format(total_duration))
    return activities, times_by_issue_id, total_duration


def syncToGitlab(times_by_issue_id, date):
    '''Push all given time_entries to Gitlab'''

    # Init Gitlab object
    gl = gitlab.Gitlab(config.get('gitlab', 'url'), config.get('gitlab', 'project_id'), config.get('gitlab', 'token'))

    # Synch
    print_("-> Sending entries")
    try:
        for issue_id, total in times_by_issue_id.items():
            print_('.')
            try:
                # Send this activity to Gitlab
                gl.add_time_entry(issue_id, "{}h".format(total))
            except gitlab.GitlabException:
                print()
                print("Error sending {!r}".format((issue_id, total)))
                raise
    except ConnectionError as e:
        print("Connection Error: {}".format(e.message))
    print("\n")


if __name__ == '__main__':
    # Read config file
    if not os.path.isfile(CONFIG_FILE):
        print(('Can\'t find config file: {}\nYou can copy template conf file and adapt.'.format(CONFIG_FILE)))
        sys.exit(-1)

    config = RawConfigParser(inline_comment_prefixes=(';',))
    config.read(CONFIG_FILE)

    # Parse command line parameters
    args = docopt(DOC.format(self_name=os.path.basename(__file__)))
    from_date, to_date, for_date = common.parse_dates_in_args(args, config)

    # logging config
    logging.basicConfig(format="%(levelname)s: %(message)s", level=(logging.DEBUG if args['--debug'] else logging.INFO))

    # Get preferred date format from config file to display dates
    display_date_format = config.get('default', 'date_formats')
    if display_date_format.find(',') != -1:
        # More than one format is defined, take first
        display_date_format = (display_date_format.split(',')[0]).strip()

    # print confirmation to user, to check dates
    if from_date:
        if to_date is None:
            # implicitly takes today for to_date
            to_date = arrow.now()
            question = "Sync tasks from {} to today (included) ?".format(from_date.format(display_date_format))
        else:
            question = "Sync tasks from {} to {} (included) ?".format(
                from_date.format(display_date_format),
                to_date.format(display_date_format)
            )
    elif for_date:
        if args['<date>'] == '0':
            question = "Sync tasks for today ?"
        elif args['<date>'] == '1':
            question = "Sync tasks for yesterday ({}) ?".format(for_date.format(display_date_format))
        else:
            question = "Sync tasks for {} ?".format(for_date.format(display_date_format))
    assert question

    if not args['--no-date-confirm']:
        print(question)
        print_("\nPress ENTER to validate ...")
        try:
            input('')
            print("\n")
        except KeyboardInterrupt:
            print("\n")
            sys.exit()

    if for_date:
        # only one date will be parsed
        from_date = for_date
        to_date = for_date
    total_time = 0
    total_sent_time = 0
    date = from_date.clone()
    while date <= to_date:
        if not for_date:
            print("{s} {formatted_date} {s}".format(s='*' * 20, formatted_date=date.format(display_date_format)))
        # Get time entries from local DB and list them in terminal
        time_entries, times_by_issue_id, day_total = getTimeEntries(date, config)
        if not time_entries:
            print("\nNo time entries to send... have you been lazy ?\n\n\n")
            date = date.shift(days=1)
            continue
        # Wait for user validation
        if not args['--auto']:
            print("\nPress ENTER to synchronize those tasks ...", end=' ')
            try:
                input('')
            except KeyboardInterrupt:
                print("\n")
                sys.exit()
        total_time += day_total
        syncToGitlab(times_by_issue_id, date)
        sent_time = math.fsum(d['duration'] for d in time_entries)
        total_sent_time += sent_time
        date = date.shift(days=1)
        print()

    print("\n---> TOTAL: {}h found in Hamster - {}h sent to Gitlab".format(round(total_time, 1), total_sent_time))

    # save question to "last_sync.txt"
    if for_date:
        text = "{}".format(from_date.format(display_date_format))
    else:
        text = "from {} to {}".format(from_date.format(display_date_format), to_date.format(display_date_format))
    with open('last_sync.txt', 'w') as _f:
        _f.write(text)
