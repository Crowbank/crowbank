import datetime
import time
from mako.template import Template
from petadmin import PetAdmin, Environment, clean_html
import argparse
import webbrowser
import decimal
import urllib2
import logging
import sys
from os import getenv, path
from settings import IMAGE_FOLDER, CONFIRMATIONS_FOLDER

log = logging.getLogger(__name__)
env = Environment()

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

env.context = 'confirm'

env.is_test = ENVIRONMENT in ('dev', 'qa')
env.configure_logger(log, ENVIRONMENT == 'dev')

log.info('Running confirm with ENVIRONMENT=%s', ENVIRONMENT)


class ReportParameters:
    def __init__(self):
        self.report = path.join(IMAGE_FOLDER, "Confirmation.html")
        self.report_txt = path.join(IMAGE_FOLDER, "Confirmation.txt")
        self.provisional_report = path.join(IMAGE_FOLDER, "PreBooking.html")
        self.provisional_report_txt = path.join(IMAGE_FOLDER, "PreBooking.txt")
        self.logo_file = path.join(IMAGE_FOLDER, "Logo.jpg")
        self.deluxe_logo_file = path.join(IMAGE_FOLDER, "deluxe_logo_2.png")
        self.pay_deposit_file = path.join(IMAGE_FOLDER, "paydeposit.png")
        self.logo_code = None
        self.deluxe_logo_code = None
        self.deposit_icon = None
        self.past_messages = []

    def read_images(self):
        with open(self.logo_file, "rb") as f:
            data = f.read()
            self.logo_code = data.encode("base64")

        with open(self.deluxe_logo_file, "rb") as f:
            data = f.read()
            self.deluxe_logo_code = data.encode("base64")

        with open(self.pay_deposit_file, "rb") as f:
            data = f.read()
            self.deposit_icon = data.encode("base64")

    @staticmethod
    def get_deposit_url(bk_no, deposit_amount, pet_names, customer, expiry = 0):
        timestamp = time.mktime(datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()).timetuple())
        timestamp += expiry * 24 * 3600
        timestamp *= 1000
        fee = decimal.Decimal(1.20)

        url = "https://secure.worldpay.com/wcc/purchase?instId=1094566&cartId=PBL-%d&amount=%f&currency=GBP&" %\
              (bk_no, deposit_amount + fee)
        url += 'desc=Deposit+for+Crowbank+booking+%%23%d+for+%s&accId1=CROWBANKPETBM1&testMode=0' %\
               (bk_no, urllib2.quote(pet_names))
        url += '&name=%s' % urllib2.quote(customer.display_name())
        if customer.email != '':
            url += '&email=%s' % urllib2.quote(customer.email)
        if customer.addr1 != '':
            url += '&address1=%s' % urllib2.quote(customer.addr1)
        if customer.addr2 != '':
            url += '&address2=%s' % urllib2.quote(customer.addr2)
        if customer.addr3 != '':
            url += '&town=%s' % urllib2.quote(customer.addr3)
        if customer.postcode != '':
            url += '&postcode=%s' % urllib2.quote(customer.postcode)
        url += '&country=UK'
        if expiry:
            url += '`%d' % timestamp

        if customer.telno_home != '':
            phone = customer.telno_home
            if len(phone) == 6:
                phone = '01236 ' + phone
            url += '&tel=%s' % urllib2.quote(phone)

        return url


class ConfirmationCandidate:
    """
    A class representing a candidate for confirmation generation.
    """
    def __init__(self, petadmin, bk_no):
        self.bk_no = bk_no
        self.new = False        # a new booking - any subsequent amendments are 'swallowed'
        self.payment = False    # flag determining whether a payment is acknowledged
        self.amended = False    # flag determining whether this is an amendment of an existing booking
        self.booking = petadmin.bookings.get(bk_no)
        if self.booking:
            self.pet_names = self.booking.pet_names()

        self.deposit = True     # flag determining whether a deposit request is necessary
        self.deposit_amount = decimal.Decimal("0.00")
        self.conf_no = 0
        self.payment_amount = decimal.Decimal("0.00")
        self.payment_date = None
        self.title = ''
        self.forced_subject = ''
        self.deluxe = False
        self.env = petadmin.env
        self.booking_count = 0
        self.past_messages = []
        self.force_deposit = False
        self.in_next_year = False
        self.next_years_prices = False
        self.deposit_url = ''
        self.additional_text = ''
        if self.booking:
            self.cancelled = self.booking.status == 'C'
            self.standby = self.booking.status == 'S'
            self.skip = (self.booking.skip == 1)

    def add_event(self, aud_type, aud_action, aud_amount, aud_date):
        if aud_type == 'P' and aud_action == 'A':
            self.payment = True
            self.payment_amount = aud_amount
            self.payment_date = aud_date

        elif aud_type == 'B':
            if aud_action == 'A':
                self.new = True
                self.amended = False
            elif aud_type == 'A' and not self.new:
                self.amended = True
            if aud_action == 'C':
                self.cancelled = True

    def prepare(self, report_parameters=None):
        if not self.booking:
            return

#        if self.booking.start_date.year > 2017:
#            self.in_next_year = True

#        if self.booking.start_date.month > 3 and self.booking.start_date.year > 2017:
#            self.next_years_prices = True#

        if self.booking is None:
            raise RuntimeError("Missing booking objects")

        if self.booking.deluxe == 1:
            self.deluxe = True

        if not self.force_deposit:
            if self.standby:
                log.debug('Standby - no deposit')
                self.deposit = False

 #           if self.deposit and self.in_next_year:
 #               log.debug('Next year booking - no deposit')
 #               self.deposit = False

            if self.deposit and self.booking.status == 'V':
                log.debug('Booking status confirmed - no deposit')
                self.deposit = False

            if self.deposit and self.booking.paid_amt != decimal.Decimal("0.00"):
                log.debug('Booking with prior payments - no deposit')
                self.deposit = False

            if self.deposit and self.booking.customer.nodeposit:
                log.debug('Booking with no-deposit customer - no deposit')
                self.deposit = False

            if self.deposit and self.booking.peak == 0:
                log.debug('Booking during off-peak - no deposit')
                self.deposit = False

            if self.deposit and self.payment_amount != decimal.Decimal("0.00"):
                log.debug('Booking associated with payment event - no deposit')
                self.deposit = False

#             if self.deposit and self.booking.customer.deposit_requested:
#                 log.debug('Booking deposit already requested for same customer')
#                 self.deposit = False

        if self.deposit:
            if self.deposit_amount == decimal.Decimal("0.00"):
                self.deposit_amount = decimal.Decimal("30.00")
                for pet in self.booking.pets:
                    if pet.spec == 'Dog':
                        self.deposit_amount = decimal.Decimal("50.00")
                if self.deposit_amount > self.booking.gross_amt / 2:
                    self.deposit_amount = decimal.Decimal(self.booking.gross_amt) / 2

            if not report_parameters:
                report_parameters = ReportParameters()

            self.deposit_url = report_parameters.get_deposit_url(self.booking.no, self.deposit_amount,
                                                                 self.booking.pet_names(), self.booking.customer)

        if self.cancelled:
            self.title = 'Booking Cancellation'
        elif self.standby:
            self.title = 'Standby Booking'
        else:
            if self.deposit:
                if self.deluxe:
                    self.title = 'Provisional Deluxe Booking'
                else:
                    self.title = 'Provisional Booking'
            else:
                if self.deluxe:
                    self.title = 'Confirmed Deluxe Booking'
                else:
                    self.title = 'Confirmed Booking'

            if self.amended:
                self.title += ' - Amended'

        self.clean_additional_text = clean_html(self.additional_text)

    def confirmation_body(self, report_parameters=None, body_format='html'):
        if not self.booking:
            return

        self.pet_names = self.booking.pet_names()
        today_date = datetime.date.today()

        if not report_parameters:
            report_parameters = ReportParameters()
            report_parameters.read_images()

        if body_format == 'html':
            mytemplate = Template(filename=report_parameters.report)
        else:
            mytemplate = Template(filename=report_parameters.report_txt)

        self.paid = self.booking.paid_amt <> decimal.Decimal(0.00)

        body = mytemplate.render(today_date=today_date, conf=self, logo_code=report_parameters.logo_code,
                                 deposit_icon=report_parameters.deposit_icon,
                                 deluxe_logo_code=report_parameters.deluxe_logo_code,
                                 deposit_url=self.deposit_url)

        return body

    def generate_confirmation(self, report_parameters, action):
        if not self.booking:
            log.error('Missing booking')
            return

        log.debug('Generating confirmation for booking %d, action = %s', self.booking.no, action)

        if self.skip:
            log.warning('Skipping booking %d', self.booking.no)
            return

        self.prepare(report_parameters)
        log.info('Booking %d titled %s. Action: %s', self.booking.no, self.title, action)

        body = self.confirmation_body(report_parameters)
        body_txt = self.confirmation_body(report_parameters, body_format='txt')

        now = datetime.datetime.now()
        text_file_name = "%d_%s.txt" % (self.booking.no, now.strftime("%Y%m%d%H%M%S"))
        fout = path.join(CONFIRMATIONS_FOLDER, text_file_name)
        f = open(fout, 'w')
        f.write(body_txt)
        f.close()

        file_name = "%d_%s.html" % (self.booking.no, now.strftime("%Y%m%d%H%M%S"))
        fout = path.join(CONFIRMATIONS_FOLDER, file_name)
        f = open(fout, 'w')
        f.write(body)
        f.close()

        send_email = False
        if action == 'email':
            send_email = True

        if action == 'display' or action == 'review':
            webbrowser.open_new_tab(fout)

        if action == 'review':
            response = raw_input("Email message [Y/N]? ")
            send_email = (response.lower()[0] == 'y')

        if send_email:
            if self.booking.customer.email == '':
                log.warning('Customer %d (%s) has no email address [bk_no=%d]', self.booking.customer.no,
                            self.booking.customer.surname, self.booking.no)
            else:
                if self.forced_subject:
                    subject = self.forced_subject
                else:
                    subject = '%s #%d' % (self.title, self.booking.no)

#                for past_message in self.past_messages:
#                    if past_message[1] == self.booking.customer.email and past_message[2] == subject\
#                            and now() - past_message[0] < 7:
#                        log.warning('Email to %s skipped - identical email already sent on %s', past_message[1],
#                                    past_message[0])
#                        return

                self.env.send_email(self.booking.customer.email, body, subject, body_txt)

                try:
                    if not self.deposit:
                        self.deposit_amount = 0.0
                    handle_confirmation(self.booking.no, self.deposit_amount, subject, file_name, self.conf_no,
                                        self.booking.customer.email)
                except Exception as e:
                    log.exception(e.message)

        log.debug('Confirmation complete')


def handle_confirmation(bk_no, deposit_amount, subject, file_name, conf_no=0, email = ''):
    sql = "Execute pinsert_confaction %d, %d, '', '%s', '%s', %f, '%s'" %\
        (conf_no, bk_no, subject, file_name, deposit_amount, email)
    env.execute(sql)


def handle_remote_confirmation(data):
    code = 1
    error_message = ''

    try:
        bk_no = data['bk_no']
        deposit_requested = 'deposit_amount' in data
        deposit_amount = 0.0
        if deposit_requested:
            deposit_amount = data['deposit_amount']

        body = data['body']
        file_name = data['file_name']
        subject = data['subject']
        destination = data['email']

        fout = "Z:\Kennels\Confirmations\%s" % file_name
        f = open(fout, 'w')
        f.write(body)
        f.close()

        handle_confirmation(bk_no, deposit_amount, subject, fout, 0, destination)
    except Exception as e:
        code = 0
        error_message = e.message

    return code, error_message


def confirm_all(petadmin, report_parameters, action, asofdate=None, audit_start=0, additional_text='', forced_subject=''):
    confirmation_candidates = {}
    conf_time = datetime.datetime.now()

    cursor = env.get_cursor()
# start by reading all past emails sent, to safeguard against double-sending

    sql = """select hist_bk_no, hist_date, hist_destination, hist_subject from vwhistory
        where hist_report = 'Conf-mail' and hist_type = 'Email Client'"""
    try:
        cursor.execute(sql)
    except Exception as e:
        log.exception("Exception executing '%s': %s", sql, e.message)
        return

    past_messages = {}

    for row in cursor:
        bk_no = row[0]
        hist_date = row[1]
        destination = row[2]
        subject = row[3]
        if bk_no not in past_messages:
            past_messages[bk_no] = []
        past_messages[bk_no].append((hist_date, destination, subject))

    if asofdate:
        sql = """select a.bk_no, aud_type, aud_action, aud_amount, aud_date, aud_booking_count from vwaudit a
        join vwbooking b on a.bk_no = b.bk_no
        where b.bk_start_date > GETDATE() and aud_date >= '%s' order by b.bk_start_date""" % asofdate
    elif audit_start > 0:
        sql = """select a.bk_no, aud_type, aud_action, aud_amount, aud_date, aud_booking_count from vwaudit a
        join vwbooking b on a.bk_no = b.bk_no
        where b.bk_start_date > GETDATE() and aud_no > %d order by b.bk_start_date""" % audit_start
    else:
        sql = """select a.bk_no, aud_type, aud_action, aud_amount, aud_date, aud_booking_count, aud_confirm
        from vwrecentaudit a
        join vwbooking b on a.bk_no = b.bk_no
        where b.bk_start_date > GETDATE()
        order by b.bk_start_date"""

    try:
        cursor.execute(sql)
    except Exception as e:
        log.exception("Exception executing '%s': %s", sql, e.message)
        return

    rows = cursor.fetchall()

    for row in rows:
        bk_no = row[0]
        aud_type = row[1]
        aud_action = row[2]
        aud_amount = row[3]
        aud_date = row[4]
        aud_booking_count = row[5]
        aud_confirm = row[6]

        env.set_key(bk_no, 'B')

        log.debug('Processing audit event for booking %d, type %s, action %s', bk_no, aud_type, aud_action)
        if not aud_confirm:
            log.info('Skipping bk_no %d - no confirmation memo' % bk_no)
            continue

        if bk_no in confirmation_candidates:
            cc = confirmation_candidates[bk_no]
        else:
            cc = ConfirmationCandidate(petadmin, bk_no)
            cc.additional_text = additional_text
            cc.forced_subject = forced_subject
            if not cc.booking:
                log.error('Missing booking for bk_no = %d' % bk_no)
                continue

            if cc.booking.status == 'S':
                log.info('Skipping booking #%d - status is %s', bk_no, cc.booking.status)
                continue

            if bk_no in past_messages:
                cc.past_messages = past_messages[bk_no]
            confirmation_candidates[bk_no] = cc
            cc.booking = petadmin.bookings.get(bk_no)

        cc.add_event(aud_type, aud_action, aud_amount, aud_date)
        cc.booking_count = aud_booking_count

    env.clear_key()
    log.info('Confirming %d candidates', len(confirmation_candidates))
    if len(confirmation_candidates) > 0:
        sql = "Insert into tblconfirm (conf_time, conf_candidates) values ('%s', %d)" %\
              (conf_time.strftime('%Y%m%d %H:%M:%S'), len(confirmation_candidates))
        try:
            env.execute(sql)
        except Exception as e:
            log.exception("Exception executing '%s': %s", sql, e.message)
            return

        sql = 'Select @@Identity'
        try:
            cursor.execute(sql)
        except Exception as e:
            log.exception("Exception executing '%s': %s", sql, e.message)
            return

        row = cursor.fetchone()
        conf_no = row[0]

        log.debug('Created confirmation record #%d with %d candidates', conf_no, len(confirmation_candidates))

        successfuls = 0
        for cc in confirmation_candidates.values():
            env.set_key(cc.booking.no, 'B')
            log.debug('Processing confirmation candidate')
            cc.conf_no = conf_no
            try:
                cc.generate_confirmation(report_parameters, action)
                log.debug('Generate confirmation completed successfully')
                successfuls += 1
            except Exception as e:
                log.exception('Exception when generating confirmation for booking %d: %s', cc.booking.no,
                              e.message)
        env.clear_key()
        sql = 'Update tblconfirm set conf_successfuls = %d where conf_no = %d' % (successfuls, conf_no)
        env.execute(sql)

    sql = 'Execute pmaintenance'
    try:
        env.execute(sql)
    except Exception as e:
        log.exception("Exception executing '%s': %s", sql, e.message)
        return


def process_booking(bk_no, args, pa, action, rp, additional_text='', forced_subject=''):
    cc = ConfirmationCandidate(pa, bk_no)
    cc.additional_text = additional_text
    cc.forced_subject = forced_subject
    if args.confirmed:
        cc.booking.status = 'V'
    if args.deposit is not None:
        cc.force_deposit = True
        cc.deposit_amount = decimal.Decimal(args.deposit)
    if args.payment is not None:
        cc.payment = True
        cc.payment_amount = decimal.Decimal(args.payment)
    if args.amended:
        cc.amended = True
    if args.cancel:
        cc.cancelled = True
    if args.deluxe:
        cc.deluxe = True
    cc.skip = False
    cc.generate_confirmation(rp, action)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-booking', nargs='*', action='store', type=int, help='Booking number(s)')
    parser.add_argument('-confirmed', action='store_true', help='Use to treat booking as confirmed')
    parser.add_argument('-deposit', action='store', help='Deposit amount to be requested')
    parser.add_argument('-amended', action='store_true', help='Use to indicate an amended booking')
    parser.add_argument('-payment', action='store', help='Payment amount to be acknowledged')
    parser.add_argument('-cancel', action='store_true', help='Send cancellation confirmation')
    parser.add_argument('-deluxe', action='store_true', help='Treat booking as Deluxe')
    parser.add_argument('-display', help='Display report in browser - no email', action='store_true')
    parser.add_argument('-file', help='Only generate html file - no email, no browser', action='store_true')
    parser.add_argument('-review', action='store_true',
                        help="""Use with command line - display each confirmation and ask
for approval to send to customer""")
    parser.add_argument('-audit_start', help='Run for all audit events > AUDIT_START', action='store')
    parser.add_argument('-all', help='Generate report for every booking since last report generation',
                        action='store_true')
    parser.add_argument('-asofdate', help='Generate report for every booking since ASOFDATE [yyyymmdd]',
                        action='store')
    parser.add_argument('-last', help='Confirm the last booking in the database', action='store_true')
    parser.add_argument('-stay', help='Keep window open when done', action='store_true')
    parser.add_argument('-env', help='Choose environemnt (prod/qa/dev)', action='store')
    parser.add_argument('-add', help='Additional Text', action='store')
    parser.add_argument('-subject', help='Override subject', action='store')

    args = parser.parse_args()

    action = 'email'
    if args.display:
        action = 'display'
    if args.file:
        action = 'file'
    if args.review:
            action = 'review'

    log.info('Running %s', ' '.join(sys.argv))

    rp = ReportParameters()
    rp.read_images()

    pa = PetAdmin(env)
    pa.load()

    audit_start = 0
    if args.audit_start:
        audit_start = int(args.audit_start)

    additional_text = ''
    if args.add:
        additional_text = args.add

    forced_subject = ''
    if args.subject:
        forced_subject = args.subject

    if args.all:
        env.context = 'confirm_all'
        confirm_all(pa, rp, action, args.asofdate, audit_start, additional_text, forced_subject)

        return
#            cc.generate_confirmation(conf_no, cc.bk, cc.new_booking, cc.has_payment, cc.changed_dates, args.deposit,
#                                  args.report, logo_code, deposit_icon, args.test)
    else:
        if args.last:
            bk_no = max(pa.bookings.bookings.keys())
            process_booking(bk_no, args, pa, action, rp, additional_text, forced_subject)
        else:
            if args.booking:
                for bk_no in args.booking:
                    process_booking(bk_no, args, pa, action, rp, additional_text, forced_subject)

    env.close()
    if args.stay:
        raw_input("Hit any key to close window")


def test_url_expiry():
    pa = PetAdmin(env)
    pa.load()
    bk_no = 6229
    booking = pa.bookings.get(bk_no)
    deposit_amount = 50.0
    pet_names = ''
    customer = ''
    for i in range(0, 3):
        expiry = i / 2.0 + 0.1
        deposit_url = ReportParameters.get_deposit_url(booking.no, deposit_amount, booking.pet_names(),
                                                       booking.customer, expiry)
        print('expiry in %f days: %s' % (expiry, deposit_url))

if __name__ == '__main__':
    main()
#    test_url_expiry()
