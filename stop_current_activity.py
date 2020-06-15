#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# Simple script to stop current activity (hamster-cli didn't worked for me)

from pathlib import Path
import sqlite3
import sys
from configparser import RawConfigParser

import moment

CONFIG_FILE = 'gitlabtimesync.config'

if __name__ == '__main__':
    # Read config file
    config_file = Path(__file__).parent / CONFIG_FILE
    if not config_file.exists():
        print(('Can\'t find config file: {}\nYou can copy template conf file and adapt.'.format(CONFIG_FILE)))
        sys.exit(-1)
    config = RawConfigParser()
    config.read(config_file)
    db_filename = config.get('default', 'db')
    # Stop current activity
    now_str = moment.now().format("YYYY-MM-DD HH:mm:ss")
    connection = sqlite3.connect(Path(db_filename).expanduser())
    dbCursor = connection.cursor()
    dbCursor.execute("UPDATE facts SET end_time = ? WHERE end_time IS NULL LIMIT 1;", (now_str, ))
    connection.commit()
    connection.close()
