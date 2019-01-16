#!/usr/bin/python
from pypa.petadmin import PetAdmin
from pypa.env import Environment, clean_html, log, ENVIRONMENT
import argparse
from pypa.confirmation import ReportParameters, confirm_all, process_booking
import sys


def main():
    env = Environment('confirm')
    env.configure_logger(log)

    log.info(f'Running confirm with ENVIRONMENT={ENVIRONMENT}')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-booking',
        nargs='*',
        action='store',
        type=int,
        help='Booking number(s)')
    parser.add_argument(
        '-confirmed',
        action='store_true',
        help='Use to treat booking as confirmed')
    parser.add_argument(
        '-deposit',
        action='store',
        help='Deposit amount to be requested')
    parser.add_argument(
        '-amended',
        action='store_true',
        help='Use to indicate an amended booking')
    parser.add_argument(
        '-payment',
        action='store',
        help='Payment amount to be acknowledged')
    parser.add_argument(
        '-cancel',
        action='store_true',
        help='Send cancellation confirmation')
    parser.add_argument(
        '-deluxe',
        action='store_true',
        help='Treat booking as Deluxe')
    parser.add_argument(
        '-display',
        help='Display report in browser - no email',
        action='store_true')
    parser.add_argument(
        '-file',
        help='Only generate html file - no email, no browser',
        action='store_true')
    parser.add_argument(
        '-review',
        action='store_true',
        help=(
            'Use with command line - display each confirmation and ask '
            'for approval to send to customer'))
    parser.add_argument(
        '-audit_start',
        help='Run for all orphan audit events > AUDIT_START',
        action='store')
    parser.add_argument(
        '-all',
        help='Generate report for every booking since last report generation',
        action='store_true')
    parser.add_argument(
        '-asofdate',
        help='Generate report for every booking since ASOFDATE [yyyymmdd]',
        action='store')
    parser.add_argument(
        '-last',
        help='Confirm the last booking in the database',
        action='store_true')
    parser.add_argument(
        '-stay',
        help='Keep window open when done',
        action='store_true')
    parser.add_argument(
        '-env',
        help='Choose environemnt (prod/qa/dev)',
        action='store')
    parser.add_argument(
        '-add',
        help='Additional Text',
        action='store')
    parser.add_argument(
        '-subject',
        help='Override subject',
        action='store')

    args = parser.parse_args()

    action = 'email'
    if args.display:
        action = 'display'
    if args.file:
        action = 'file'
    if args.review:
        action = 'review'

    arguments = ' '.join(sys.argv)
    log.info(f'Running {arguments}')

    rp = ReportParameters(env)
    rp.read_images()

    pa = PetAdmin(env)

    audit_start = 0
    if args.audit_start:
        audit_start = args.audit_start

    additional_text = ''
    if args.add:
        additional_text = args.add

    forced_subject = ''
    if args.subject:
        forced_subject = args.subject

    if args.all:
        env.context = 'confirm_all'
        confirm_all(pa, rp, action, args.asofdate, audit_start,
                    additional_text, forced_subject)

        return

    else:
        if args.last:
            pa.load()
            bk_no = max(pa.bookings.bookings.keys())
            process_booking(
                bk_no, args, pa, action, rp, additional_text,
                forced_subject)
        else:
            if args.booking:
                pa.load()
                for bk_no in args.booking:
                    process_booking(
                        bk_no, args, pa, action, rp,
                        additional_text, forced_subject)

    env.close()
    if args.stay:
        input("Hit any key to close window")


if __name__ == '__main__':
    main()
