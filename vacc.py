#!/usr/bin/python
from petadmin import Environment
import argparse

import logging
import sys

log = logging.getLogger(__name__)
env = Environment()

def process_pet(pet_no, file_name):
    cursor = env.get_cursor()

    if file_name == '':
        file_name = 'Z:\Kennels\Vaccination Cards\%d.pdf' % pet_no

    sql = 'select pd_path from vwpetdocument where pd_pet_no = %d' % pet_no

    cursor.execute(sql)

    rows = cursor.fetchall()
    if rows:
        sql = "Execute pupdate_petdocument %d, '%s'" % (file_name, pet_no)
    else:
        sql = "Execute pinsert_petdocument %d, '%s'" % (pet_no, file_name)

    try:
        cursor.execute(sql)

    except Exception as e:
        log.exception("Exception executing '%s': %s", sql, e.message)
        return
    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pet', nargs='*', action='store', type=int, help='Pet number(s)', required=True)
    parser.add_argument('-file', action='store', help='file name [pet_no.pdf]; only applies to first pet', default='')

    args = parser.parse_args()

    env.configure_logger(log)

    log.info('Running %s', ' '.join(sys.argv))

    file_name = args.file
    for pet_no in args.pet:
        process_pet(pet_no, file_name)
        file_name = ''


if __name__ == '__main__':
    main()
