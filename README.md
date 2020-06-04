# What is this?

This is meant to help people (like me) that use both [Hamster applet](https://extensions.gnome.org/extension/425/project-hamster-extension/) (Gnome Time Tracker) and [Gitlab](https://gitlab.com/) to keep trace of activities done.

This project is based on my own "same" project for synching with Redmine; available at https://github.com/brunetton/redminetimesync

# Prerequisites

* Running Gitlab instance (with API v4)
* Gitlab personal access token (with `api` scope). See [here](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) for more details
* Python installed your local machine
* [Hamster](https://github.com/projecthamster/) running on your local machine, with at least one activity recorded

# Limitations

This scripts is limited to mono-project Gitlab; ie all issues must belong to the same Gitlab project (see below for ideas for the future)

# Installation

## Clone the repository

    git clone git@github.com:brunetton/gitlabtimesync.git

## Install needed Python packages

    pip install -r requirements.txt

## Prepare config files

Copy `gitlabtimesync.config.tpl` to `gitlabtimesync.config` : it's an INI-like file that needs two parameters:

 - url: your Gitlab public url
 - token: a Gitlab private API access token (with `api` scope). See [here](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) for more details
 - project_id: Gitlab internal ID of project containing issues (this ID is given in Gitlab's project's page just below the project's name (search for `Project ID:`))

### Using hamster-snap

When using [Snap](https://snapcraft.io/) installation ([hamster-snap](~/snap/hamster-snap/47/.local/share/hamster/hamster.db)), database file is located in `~/snap/hamster-snap/47/.local/share/hamster/hamster.db` (you may change `47` version in path). In that case, you'll have to change `db` path in `[default]` section.

# Usage

1. Log some activities in Hamster, precising Gitlab issues IDs. Valid formats are :
 - **#134: Adding some interesting stuff**
 - **Fix #243**
 - **Adding logging output (#132)**

    (you can add other custom formats, changing `issue_id_regexp` regex in configuration file)

2. run the python script: **gitlabtimesync.py**
 - to sync one day, just give the date to the script : `gitlabtimesync.py 10/10/13`
 - to sync a period, use `from` and `to` arguments : `gitlabtimesync.py from 10/10/13 to 15/10/13`
   - -> to sync from a given date until today, you don't need to precise `to` parameter : `gitlabtimesync.py from 10/10/14`

You can configure dates formats in `gitlabtimesync.config` file.

Note that all dates parameters can be also replaced by "days ago" parameters :
 - `gitlabtimesync.py 1` will sync yesterday work
 - `gitlabtimesync.py from 7` will sync last week work (from 7 days ago to today)
 - `gitlabtimesync.py from 15 to 7` will sync week before last week work (from 15 days ago to last week)

# Future ideas

- to add support to multiple projects, we could use Hamster tags/activities. For example, `#123 - this is a bug@project1` and `#123 - this is a bug@project2` could differentiate 2 different projects `project1` and `project2`

# Bonus script: stop_current_activity.py

I included a "bonus script": `stop_current_activity.py` that automatically stop current activity. I use this script with systemd to stop tracking when I put my computer in sleep mode.
