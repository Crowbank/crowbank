from petadmin import PetAdmin, Environment
import argparse
import logging
import re
from os.path import exists, join
from os import rename
from string import split


log = logging.getLogger(__name__)
env = Environment('rename_vaccination_file')

env.configure_logger(log)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-path', action='store', help='Path to directory to be scanned')
    args = parser.parse_args()

    vacc_path = r'K:\\vaccinations'

    if args.path:
        vacc_path = args.path

    sql = "select msg_no, pet_no from tblmessagepet";
    cursor = env.get_cursor()

    cursor.execute(sql)

    vacc_renames = {}
    renamed = 0
    
    for row in cursor:
        vacc_renames[row[0]] = row[1]
    
    for msg_no in vacc_renames.keys():
        filename = '-' + msg_no + '.pdf'
        if exists(join(vacc_path, filename)):
            rename(join(vacc_path, filename), join(vacc_path, vacc_names[msg_no] + '.pdf'))
            log.info('Renamed -' + msg_no + '.pdf to ' + pet_no + '.pdf')
            renamed += 1
            sql = 'delete from tblmessagepet where msg_no = ' + msg_no
            env.execute(sql)

    if renamed > 0:
        log.info('Renamed ' + renamed + ' files')

if __name__ == '__main__':
    main()
