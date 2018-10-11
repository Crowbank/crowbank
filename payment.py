#!/usr/bin/python
from datetime import date, timedelta
from petadmin import Environment
import argparse
import decimal
from os import getenv
import logging
import sys


log = logging.getLogger(__name__)
env = Environment()

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

env.context = 'payment'

log.info('Running payment with ENVIRONMENT=%s', ENVIRONMENT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('booking', action='store', type=int, help='Booking number')
    parser.add_argument('-amount', type=decimal.Decimal, action='store', help='Deposit amount. Default - requested amount', default=0.0)
    parser.add_argument('-date', action='store', help='Payment date (yyyymmdd). Default - today', default='')
    parser.add_argument('-debit', action='store_true', help='Card machine payment')
    parser.add_argument('-cash', action='store_true', help='Cash payment')
    parser.add_argument('-yesterday', action='store_true', help='Payment made yesterday')
    parser.add_argument('-debug', help='Turn on debug-level logging', action='store_true')

    pound = u'\u00A3'
    args = parser.parse_args()

    cursor = env.get_cursor()

    env.configure_logger(log, args.debug)
    env.is_test = ENVIRONMENT in ('dev', 'qa')
    env.configure_logger(log, ENVIRONMENT == 'dev')

    log.info('Running %s', ' '.join(sys.argv))

    env.set_key(args.booking, 'B')

    sql = """Select cust_surname, dbo.fnbk_pet_desc(bk_no) pets, dr_amount, bk_paid_amt
from vwbooking_simple
join vwcustomer on cust_no = bk_cust_no
left join tbldepositrequest on dr_bk_no = bk_no
where bk_no = %d""" % args.booking
    cursor.execute(sql)
    row = cursor.fetchone()
    cust_surname = row[0]
    pets = row[1]
    deposit_requested = row[2]
    paid_amt = row[3]

    if args.amount == 0.0:
        if not deposit_requested:
            log.error('No request found and no amount specified')
            return
        args.amount = deposit_requested

    deposit_type_desc = 'an online'
    deposit_type = 'Credit Card'
    if args.debit:
        deposit_type_desc = 'a card machine'
        deposit_type = 'Debit Card'
    if args.cash:
        deposit_type_desc = 'a cash'
        deposit_type = 'Cash'

    if args.date == '':
        args.date = date.today().strftime('%Y%m%d')
        if args.yesterday:
            args.date = (date.today()- timedelta(1)).strftime('%Y%m%d')

    msg = u'Processing %s deposit of %s%.2f for %s %s booking #%d' % (deposit_type_desc, pound, args.amount, pets, cust_surname, args.booking)
    print msg
    if paid_amt <> 0.0:
        msg = u'Note - a previous payment of %s%.2f has already been credited to this booking!' % (pound, paid_amt)
        print msg
    response = raw_input("Proceed? ")
    if response.lower()[0] == 'y':
        sql = "Execute ppayment %d, %f, '%s', '%s'" % (args.booking, args.amount, deposit_type, args.date)
        log.debug(sql)
        env.execute(sql)


if __name__ == '__main__':
    main()
