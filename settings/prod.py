import sys

if sys.platform == 'win32':
    LOG_FILE = 'Z:\Website\logs\crowbank.log'
else:
    LOG_FILE = '/dropbox/Website/crowbank.log'

DB_SERVER = 'HP-SERVER\\SQLEXPRESS'
DB_USER = 'PA'
DB_PWD = 'petadmin'
DB_DATABASE = 'crowbank'
