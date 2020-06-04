#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# Simple script to stop current activity (hamster-cli didn't worked for me)

import os
import sqlite3
import sys
from configparser import RawConfigParser

import moment

CONFIG_FILE = 'gitlabtimesync.config'

if __name__ == '__main__':
    # Read config file
    if not os.path.isfile(CONFIG_FILE):
        print(('Can\'t find config file: {}\nYou can copy template conf file and adapt.'.format(CONFIG_FILE)))
        sys.exit(-1)
    config = RawConfigParser()
    config.read(CONFIG_FILE)
    db_filename = config.get('default', 'db')
    # Stop current activity
    now_str = moment.now().format("YYYY-MM-DD HH:mm:ss")
    connection = sqlite3.connect(os.path.expanduser(db_filename))
    dbCursor = connection.cursor()
    dbCursor.execute("UPDATE facts SET end_time = ? WHERE end_time IS NULL LIMIT 1;", (now_str, ))
    connection.commit()
    connection.close()
