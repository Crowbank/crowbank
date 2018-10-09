#!/usr/bin/python
from petadmin import PetAdmin, Environment
import argparse
import logging
import re
from os.path import exists, join
from os import rename
from string import split
from settings import *


log = logging.getLogger(__name__)
env = Environment('rename_vaccination_file')

env.configure_logger(log)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-path', action='store', help='Path to directory to be scanned')
    args = parser.parse_args()

    vacc_path = VACC_FOLDER

    if args.path:
        vacc_path = args.path

    sql = "select msg_no, pet_no from tblmessagepet where vacc_moved = 0";
    cursor = env.get_cursor()

    cursor.execute(sql)

    vacc_renames = {}
    renamed = 0
    
    for row in cursor:
        vacc_renames[row[0]] = row[1]
    
    for msg_no in vacc_renames.keys():
        filename = '-' + str(msg_no) + '.pdf'
        if exists(join(vacc_path, filename)):
            pet_no = vacc_renames[msg_no]
            rename(join(vacc_path, filename), join(vacc_path, str(pet_no) + '.pdf'))
            log.info('Renamed -' + str(msg_no) + '.pdf to ' + str(pet_no) + '.pdf')
            renamed += 1
            sql = 'update tblmessagepet set vacc_moved = 1 where msg_no = ' + str(msg_no)
            env.execute(sql)

    if renamed > 0:
        log.info('Renamed ' + str(renamed) + ' files')

if __name__ == '__main__':
    main()
