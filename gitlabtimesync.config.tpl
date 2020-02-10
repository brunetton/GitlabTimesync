[gitlab]
# Gitlab url and private access token (see https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
url: https://my.gitlab.com
token: mygitlabsecrettoken

[default]
# Default Hamster local SQLite file
db: ~/.local/share/hamster-applet/hamster.db

# Coma-separated date formats for command line date parsing
date_formats: DD/MM/YY, DD/MM  ; first format is also used for dates display

# Regex used to parse Hamster time entry to find out issue ID
issue_id_regexp: .*# ?(\d+)
