import sys

if sys.platform == 'win32':
    LOG_FILE = 'C:\Python27\Lib\Site-packages\crowbank\logs\qa.log'
else:
    LOG_FILE = '/usr/lib/site-packages/crowbank/logs/qa.log'

DB_SERVER = 'HP-SERVER\\SQLEXPRESS_dev'
DB_USER = 'PA'
DB_PWD = 'petadmin'
DB_DATABASE = 'crowbank'
