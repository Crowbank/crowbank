from petadmin import PetAdmin, Environment
import argparse
import logging
import re
import os


log = logging.getLogger(__name__)
env = Environment()

env.configure_logger(log)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-path', action='store', help='Path to directory to be scanned')
    args = parser.parse_args()

    vacc_path = r'Z:\\kennels\\vaccination cards'
    patt = re.compile('^(\d+)\.pdf$')

    if args.path:
        vacc_path = args.path

    sql = 'select pd_pet_no, pd_path from vwpetdocument'
    cursor = env.get_cursor()

    cursor.execute(sql)

    pet_docs = {}

    for row in cursor:
        pet_docs[row[0]] = row[1]

    dirs = os.listdir(vacc_path)

    added = 0
    replaced = 0
    scanned = 0
    missing = 0

    for vacc_file in dirs:
        m = patt.match(vacc_file)
        if m:
            scanned += 1
            pet_no = int(m.group(1))
            full_path = os.path.join(vacc_path, vacc_file)

            if not (pet_no in pet_docs and
                            pet_docs[pet_no].lower().replace('\\', '') == full_path.lower().replace('\\', '')):
                if pet_no in pet_docs:
                    replaced += 1
                    log.debug('Replacing path %s with %s', pet_docs[pet_no], full_path)

                added += 1
                sql = 'Execute padd_vacc %d' % pet_no
                env.execute(sql)
                log.info('Added vaccination for pet_no = %d' % pet_no)

    added -= replaced

    log.info('Scanned %d files. Replaced %d and added %d new ones' % (scanned, replaced, added))

if __name__ == '__main__':
    main()
