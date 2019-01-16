from petadmin import Environment, PetAdmin
import argparse

import logging
import sys

log = logging.getLogger(__name__)
env = Environment()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-pet', nargs='*', action='store', type=int, help='Pet number(s)')
    parser.add_argument('-customer', action='store', type=int, help='Customer number')
    parser.add_argument('-date', action='store', help='Trial Date [yyyymmdd]', required=True)

    args = parser.parse_args()

    cursor = env.get_cursor()

    env.configure_logger(log)

    log.info('Running %s', ' '.join(sys.argv))

    pa = PetAdmin(env)
    pa.load()

    if args.customer:
        customer = pa.customers.get(args.customer)
        pets = filter(lambda p: p.spec == 'Dog', customer.pets)
    else:
        if not args.pet:
            log.error('Either customer or pet numbers must be provided')
            return
        pets = []
        for pet_no in args.pet:
            pets.append(pa.pets.get(pet_no))

        customer = pets[0].customer

    sql = "Select count(*) from vwbooking where bk_start_date = '%s' and bk_end_date = bk_start_date and bk_status in ('', 'V')" % args.date
    cursor.execute(sql)
    row = cursor.fetchone()
    c = row[0]

    if c > 1:
        response = raw_input("We already have %d other trials booked. Still go ahead [Y/N]? " % c)
        if response.lower()[0] != 'y':
            return

    sql = "Execute create_trial %d, '%s'" % (customer.no, args.date)
    cursor.execute(sql)
    row = cursor.fetchone()
    bk_no = row[0]

    for pet in pets:
        sql = "Execute add_dog_to_trial %d, %d" % (bk_no, pet.no)
        cursor.execute(sql)

    log.info('Created booking #%d' % bk_no)


if __name__ == '__main__':
    main()
