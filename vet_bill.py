from petadmin import PetAdmin, Environment
import logging
import re
import os
from datetime import date

log = logging.getLogger(__name__)
env = Environment()

env.configure_logger(log)

def main():
    bill_path = r'Z:\kennels\Vet Bills'
    patt = re.compile('^(\d+) (\d{4})-(\d{2})-(\d{2})\.pdf$')

    sql = "select pd_pet_no, pd_path from vwpetdocument where pd_desc = 'Vet Bill'"
    cursor = env.get_cursor()

    cursor.execute(sql)

    pet_docs = {}

    for row in cursor:
        if row[0] not in pet_docs:
            pet_docs[row[0]] = [[], []]
        pet_docs[row[0]][0].append(row[1])
        pet_docs[row[0]][1].append(row[1].lower().replace('\\', ''))

    dirs = os.listdir(bill_path)

    added = 0
    replaced = 0
    scanned = 0
    missing = 0

    for bill_file in dirs:
        m = patt.match(bill_file)
        if m:
            scanned += 1
            pet_no = int(m.group(1))
            bill_date = date(int(m.group(2)), int(m.group(3)), int(m.group(4)))
            full_path = os.path.join(bill_path, bill_file)

            if not (pet_no in pet_docs and 
                            full_path.lower().replace('\\', '') in pet_docs[pet_no][1]):
                added += 1
                sql = "Execute padd_bill %d, '%s'" % (pet_no, bill_date.strftime('%Y-%m-%d'))
                env.execute(sql)
                log.info('Added vet bill for pet_no = %d on %s' % (pet_no, bill_date.strftime('%d/%m/%Y')))

    log.info('Scanned %d files. Added %d new ones' % (scanned, added))

if __name__ == '__main__':
    main()
