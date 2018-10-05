import sys

if sys.platform == 'win32':
    LOG_FILE = 'C:\Python27\Lib\Site-packages\crowbank\logs\crowbank.log'
else:
    LOG_FILE = '/usr/lib/python2.7/site-packages/crowbank/logs/crowbank.log'

DB_SERVER = 'HP-SERVER\\SQLEXPRESS'
DB_USER = 'PA'
DB_PWD = 'petadmin'
DB_DATABASE = 'crowbank'
