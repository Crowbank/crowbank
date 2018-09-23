#!/usr/bin/python
from petadmin import Environment
import datetime
import argparse
import logging
import re
from os import getenv, system


log = logging.getLogger(__name__)
env = Environment()

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

log.info('Running confirm with ENVIRONMENT=%s', ENVIRONMENT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-file', action='store', help='File to import', default='TIME201.txt')
    args = parser.parse_args()

    env.is_test = ENVIRONMENT in ('dev', 'qa')
    env.configure_logger(log, ENVIRONMENT == 'dev')

    sql = "Truncate table tblclockdata_staging"
    env.execute(sql)

    filename = args.file
    out_file = filename + '.clean'
    try:
        f_in = open(filename, 'r')
    except Exception as e:
        log.error('Unable to open %s for reading', filename)
        return

    try:
        f_out = open(out_file, 'w')
    except Exception as e:
        log.error('Unable to open %s for writing', out_file)
        return

    regex = re.compile(r'^time="(?P<time>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)" id="(?P<id>\d+)" name="(?P<name>\w+)" workcode="(?P<workcode>\d+)" status="(?P<status>\d+)" authority="(?P<authority>\w+)" card_src="(?P<card_src>\w+)"')

# time="2016-03-26 13:21:05" id="3" name="LAURA" workcode="0" status="0" authority="0X11" card_src="from_check"

    f_in.readline()

    out_records = {}
    out_lines = []

    for line in f_in:
        m = regex.match(line)
        if m:
            g = m.groupdict()
            dt = datetime.datetime.strptime(g['time'], '%Y-%m-%d %H:%M:%S')
            clock_date = dt.date()
            clock_time = dt.time()
            key = clock_date.strftime('%Y%m%d') + ':' + g['id']
            if key in out_records:
                out_records[key].append(clock_time)
            else:
                out_records[key] = [clock_time]
            n = len(out_records[key])
            out_array = [clock_date.strftime('%Y%m%d'), clock_time.strftime('%H:%M:%S'), g['id'], g['name'], str(n)]
            out_line = '\t'.join(out_array) + '\n'
            out_lines.append(out_line)

    f_out.writelines(out_lines)
    f_out.close()

    f_in.close()

    cmd = 'bcp tblclockdata_staging in ./%s -c -U PA -Ppetadmin -S HP-SERVER\\SQLEXPRESS' % out_file
    system(cmd)

if __name__ == '__main__':
    main()
