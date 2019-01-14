#!/usr/bin/python
from datetime import datetime
import time
import argparse
import logging
import sys
from os import getenv
import requests
from petadmin import Environment


log = logging.getLogger(__name__)
env = Environment('check_status')

env.configure_logger(log)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', action='store', help='Target of check: local or remote')
    parser.add_argument('-fail', help='Simulate a fail', action='store_true')

    args = parser.parse_args()

        
    log.info('Running %s', ' '.join(sys.argv))

    target = args.target
    
    if target == 'local':
        url = 'http://192.168.0.200/wordpress/wp-content/plugins/crowbank/status.php'
    else:
        url = 'http://dev.crowbankkennels.co.uk/wp-content/plugins/crowbank/status.php'

    sql = "select ws_state, ws_lasttransfer from vwwebsite_state where ws_iscurrent = 1";
    cursor = env.get_cursor()

    cursor.execute(sql)

    last_fail = 0
    
    for row in cursor:
        previous_status = row[0]
        previous_lasttransfer = row[1]

    now = datetime.now()
    r = requests.get(url)
    status = r.json()
    
    age = status['age']
    lasttransfer_text = status['lasttransfer']['date']
    system_status = status['status']

    in_date_format = '%Y-%m-%d %H:%M:%S.%f'
    date_format = '%Y-%m-%d %H:%M:%S'
    lasttransfer = datetime.strptime(lasttransfer_text, in_date_format)
    lasttransfer_text = lasttransfer.strftime(date_format)
    
    new_status = 'Loaded'
    
    if age > 1200:
        new_status = 'Obsolete'
        log.error('Data age on %s system is %d seconds, last transfer on %s' % (target, age, lasttransfer))
    
    if system_status != 'Loaded':
        new_status = system_status
        log.error('Status on %s system is %s' % (target, system_status))

    if new_status == 'Loaded':
        if args.fail:
            new_status = 'Fail'
            log.error('Simulated fail on %s system' % target)
        else:
            log.info('Status on %s system is good. Last transfer, %d seconds ago, at %s' % (target, age, lasttransfer))

    if target == 'remote':
        send_email = (new_status != previous_status) or (lasttransfer != previous_lasttransfer)
    
        sql = "execute pset_website_state '%s', '%s', %d, '%s'" % (new_status, r, send_email, lasttransfer_text)
        
        env.execute(sql)
        
        if send_email:
            body = 'Remote system status changed from %s to %s. Last successful transfer was %s, %d seconds ago' % (previous_status, new_status, lasttransfer_text, age)
            subject = 'Remote system updated to %s' % new_status

            send_to = env.email_logs            
            env.send_email(send_to, body, subject, body)
    
    env.close()


if __name__ == '__main__':
    main()
