import datetime
import time
import argparse
import logging
import sys
from os import getenv
import requests
from petadmin import Environment


log = logging.getLogger(__name__)
env = Environment()

env.configure_logger(log)

env.context = 'check_status'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', action='store', help='Target of check: local or remote')

    args = parser.parse_args()

    log.info('Running %s', ' '.join(sys.argv))

    target = args.target
    
    if target == 'local':
        url = 'http://192.168.0.200/wordpress/wp-content/plugins/crowbank/status.php'
    else:
        url = 'http://dev.crowbank.co.uk/wp-content/plugins/crowbank/status.php'

    r = requests.get(url)
    status = r.json()
    
    age = status['age']
    lasttransfer = status['lasttransfer']['date']
    system_status = status['status']

    age = 1300
    system_status = 'Unloaded'
    
    if age > 1200:
        log.error('Data age on %s system is %d seconds, last transfer on %s' % (target, age, lasttransfer))
    
    if system_status != 'Loaded':
        log.error('Status on %s system is %s' % (target, system_status))

if __name__ == '__main__':
    main()
