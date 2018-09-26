import sys

if sys.platform == 'win32':
    LOG_FILE = 'C:\Python27\Lib\Site-packages\petadmin\logs\crowbank.log'
else:
    LOG_FILE = '/usr/lib/site-packages/crowbank/logs/crowbank.log'

DB_SERVER = 'HP-SERVER\\SQLEXPRESS'
DB_USER = 'PA'
DB_PWD = 'petadmin'
DB_DATABASE = 'crowbank'
