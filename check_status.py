from datetime import datetime
import time
import argparse
import logging
import sys
from os import getenv
import requests
from petadmin import Environment

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

log = logging.getLogger(__name__)
env = Environment()

env.configure_logger(log)

env.context = 'check_status'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', action='store', help='Target of check: local or remote')
    parser.add_argument('-env', help='Choose environemnt (prod/qa/dev)', action='store')

    args = parser.parse_args()

    log.info('Running %s', ' '.join(sys.argv))

    if args.env:
        ENVIRONMENT = args.env
        
    target = args.target
    
    if target == 'local':
        url = 'http://192.168.0.200/wordpress/wp-content/plugins/crowbank/status.php'
    else:
        url = 'http://dev.crowbankkennels.co.uk/wp-content/plugins/crowbank/status.php'

    sql = "select max(rs_lasttransfer) from tblremotestatus where rs_sev_no > 1";
    cursor = env.get_cursor()

    cursor.execute(sql)

    last_fail = 0
    
    for row in cursor:
        last_fail = row[0]

    now = datetime.now()
    r = requests.get(url)
    status = r.json()
    
    age = status['age']
    lasttransfer = status['lasttransfer']['date']
    system_status = status['status']

    in_date_format = '%Y-%m-%d %H:%M:%S.%f'
    date_format = '%Y-%m-%d %H:%M:%S'
    lasttransfer = datetime.strptime(lasttransfer, in_date_format)
    
    sev_no = 1
    
    if (lasttransfer == last_fail):
        return
    
    if age > 1200:
        sev_no = 3
        log.error('Data age on %s system is %d seconds, last transfer on %s' % (target, age, lasttransfer))
    
    if system_status != 'Loaded':
        sev_no = 3
        log.error('Status on %s system is %s' % (target, system_status))

    if sev_no < 3:
        log.info('Status on %s system is good. Last transfer, %d seconds ago, at %s' % (target, age, lasttransfer))

    sql = "Execute premotestatus '%s', '%s', %d, '%s', %d" % \
        (now.strftime(date_format), system_status, age, lasttransfer.strftime(date_format), sev_no)
    
    cursor.execute(sql)
    env.close()


if __name__ == '__main__':
    main()
