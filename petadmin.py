import sys
if sys.platform == 'win32':
    import pymssql
if sys.platform == 'cygwin':
    import pyodbc
import datetime
import decimal
import smtplib
import logging
import logging.handlers
import re
from os import getenv

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

log = logging.getLogger(__name__)

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

from crowbank.settings import *

TAG_RE = re.compile(r'<[^>]+>')

def clean_html(html_text: str) -> str:
    return TAG_RE.sub('', html_text)


class DatabaseHandler(logging.Handler):
    def __init__(self, env):
        logging.Handler.__init__(self)
        self.env = env

    def emit(self, record):
        msg = self.format(record)
        levelname = record.levelname
        filename = record.filename
        lineno = record.lineno
        sql = f"""
Execute plog '{msg.replace("'", "''")}', '{level_name}', '{self.env.context}',
{self.env.key}, '{self.env.key_type}',
'{filename}', {lineno})"""

        self.env.execute(sql)


class BufferingSMTPHandler(logging.handlers.BufferingHandler):
    def __init__(self, env):
        logging.handlers.BufferingHandler.__init__(self, 1000)
        self.env = env
        self.mailhost = env.email_host
        self.mailport = None
        self.fromaddr = env.email_user
        self.toaddrs = env.email_logs
        self.subject = 'Python Log'
        self.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-7s %(message)s"))

    def flush(self):
        if len(self.buffer) > 0:
            try:
                body = ''
                for record in self.buffer:
                    s = self.format(record)
                    body += s + "<br/>"

                self.env.send_email(self.toaddrs, body, self.subject, body, True)
            except Exception:
                self.handleError(None)  # no particular record
            self.buffer = []


class Environment:
    def __init__(self, context, env_type = ''):
        if not env_type:
            if ENVIRONMENT:
                env_type = ENVIRONMENT
            else:
                env_type = 'prod'
                
        self.env_type = env_type
        self.platform = sys.platform
        self.email_host = EMAIL_HOST
        self.email_user = EMAIL_USER
        self.email_bcc = EMAIL_BCC
        self.email_pwd = EMAIL_PWD
        self.email_logs = EMAIL_LOGS
        self.email_replyto = EMAIL_REPLYTO
        self.smtp_server = None
        self.connection = None
        self.is_test = (env_type in ('qa', 'dev'))
        self.smtp_handler = None
        self.crowbank_addresses = CROWBANK_ADDRESSES
        self.context = context
        self.key = 0
        self.key_type = ''
        

    def set_key(self, key, key_type):
        self.key = key
        self.key_type = key_type

    def clear_key(self):
        self.key = 0
        self.key_type = ''

    def get_smtp_server(self):
        if self.smtp_server:
            if self.smtp_server.noop()[0] == 250:
                return self.smtp_server
            self.smtp_server.connect(self.email_host)
        else:
            self.smtp_server = smtplib.SMTP_SSL(self.email_host, 465, timeout=120)
        self.smtp_server.ehlo()
        self.smtp_server.login(self.email_user, self.email_pwd)

        return self.smtp_server

    def configure_logger(self, logger):
        log_file = LOG_FILE
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file, when='W0')
        
        debug = (self.env_type in ('qa', 'dev'))

        self.smtp_handler = BufferingSMTPHandler(self)
        stream_handler = logging.StreamHandler()
        if not self.smtp_server:
            try:
                self.get_smtp_server()
            except Exception:
                logger.error('Unable to connect to smtp server')

        formatter = logging.Formatter(
            '%(asctime)s  [%(levelname)-5s] %(message)s')
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        self.smtp_handler.setFormatter(formatter)

        db_handler = DatabaseHandler(self)

        logger.addHandler(file_handler)
        logger.addHandler(self.smtp_handler)
        logger.addHandler(stream_handler)
        logger.addHandler(db_handler)

        if self.is_test or debug:
            logger.setLevel(logging.DEBUG)
            self.smtp_handler.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.INFO)
            self.smtp_handler.setLevel(logging.WARNING)

    def get_connection(self):
        if not self.connection:
            if self.platform == 'win32':
                self.connection = pymssql.connect(
                    server=DB_SERVER, user=DB_USER, password=DB_PWD,
                    database=DB_DATABASE)
            else:
                driver = 'SQL SERVER'
                self.connection = pyodbc.connect(
f"""DRIVER={driver};SERVER={DB_SERVER};DATABASE={DB_DATABASE};
UID={DB_USER};PWD={DB_PWD}"""
                    )

        return self.connection

    def get_cursor(self):
        conn = self.get_connection()
        cur = conn.cursor()
        return cur

    def execute(self, sql, commit = True):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql)
            if commit:
                conn.commit()
        except Exception as e:
            log.error(f'Error executing {sql}: {e}')

    def send_email(
        self, send_to, send_body, send_subject, alt_body, force_send=False
    ):
        msg = MIMEMultipart('alternative')

        if self.env_type != "prod":
            send_subject += f' ({ENVIRONMENT})'
            send_to = self.email_bcc

        msg['Subject'] = send_subject
        msg['From'] = self.email_user
        msg['To'] = send_to
        msg['Date'] = formatdate(localtime=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        msg['Message-Id'] = f'{timestamp}@crowbank.co.uk'

        part1 = MIMEText(alt_body, 'plain')
        part2 = MIMEText(send_body, 'html')

        msg.attach(part1)
        msg.attach(part2)

        try:
            server = self.get_smtp_server()
            server.sendmail(self.email_user, [send_to], msg.as_string())

        except smtplib.SMTPServerDisconnected as e:
            self.smtp_server.connect()
            server.sendmail(self.email_user, [send_to], msg.as_string())

    def send_email_old(self, send_to, send_body, send_subject, force_send=False):
        target = [send_to]
        if ENVIRONMENT != "prod":
            send_subject += f' ({ENVIRONMENT})'
            target = [self.email_bcc]
        msg = f"""
To:{send_to}\nMIME-Version: 1.0\nContent-type: text/html\n
From: Crowbank Kennels and Cattery <{self.email_user}>\n
Subject:{send_subject}\n
\n
{send_body}"""

        try:
            server = self.get_smtp_server()
            server.sendmail(self.email_user, target, msg)
        except smtplib.SMTPServerDisconnected as e:
            self.smtp_server.connect()
            self.smtp_server.sendmail(self.email_user, target, msg)

    def close(self):
        if self.connection:
            self.connection.close()
        if self.smtp_handler:
            self.smtp_handler.flush()


class PetAdmin:
    def __init__(self, env):
        self.env = env
        self.customers = Customers(env)
        self.breeds = Breeds(env)
        self.pets = Pets(env, self.customers, self.breeds)
        self.services = Services(env)
        self.bookings = Bookings(env, self.customers, self.pets, self.services)
        self.runs = Runs(env, self.bookings, self.pets)
        self.loaded = False

    def load(self, force=False):
        if self.loaded and not force:
            return

        log.debug('Loading PetAdmin')
        self.customers.load(force)
        self.pets.load(force)
        self.services.load(force)
        self.bookings.load(force)
        self.runs.load(force)

        self.loaded = True
        log.debug('Loading PetAdmin Complete')
    
    def load_customer(self, cust_no):
        if self.loaded:
            return
        
        log.debug(f'Loading customer #{cust_no}')
        self.services.load()
        self.customers.load_one(cust_no)
        self.pets.load_for_customer(cust_no)
        self.bookings.load_for_customer(cust_no)


class Customers:
    def __init__(self, env):
        self.customers = {}
        self.env = env
        self.loaded = False

    def get(self, cust_no):
        if cust_no in self.customers:
            return self.customers[cust_no]
        else:
            return None

    def load_by_sql(self, sql):
        cursor = self.env.get_cursor()

        cursor.execute(sql)
        for row in cursor:
            cust_no = row[0]
            customer = Customer(cust_no)
            customer.surname = row[1]
            customer.forename = row[2]
            customer.addr1 = row[3]
            customer.addr2 = row[4]
            customer.addr3 = row[5]
            customer.postcode = row[6]
            customer.telno_home = row[7]
            customer.email = row[8]
            customer.discount = row[9]
            customer.telno_mobile = row[10]
            customer.title = row[11]
            customer.nodeposit = row[12]
            customer.deposit_requested = row[13]
            customer.nosms = row[14]

            self.customers[cust_no] = customer

    def load(self, force=False):
        if self.loaded and not force:
            return

        log.debug('Loading Customers')

        sql = """
Select cust_no, cust_surname, cust_forename, cust_addr1, cust_addr2,
cust_addr3, cust_postcode, cust_telno_home, cust_email, cust_discount,
cust_telno_mobile, cust_title, cust_nodeposit, cust_deposit_requested,
cust_nosms from vwcustomer"""

        self.load_by_sql(sql)

        log.debug(f'Loaded {len(self.customers)} customers')
        self.loaded = True

    def load_one(self, cust_no):
        if self.loaded or cust_no in self.customers:
            return
        
        log.debug(f'Loading customer #{cust_no}')

        sql = f"""
Select cust_no, cust_surname, cust_forename, cust_addr1, cust_addr2, cust_addr3,
cust_postcode, cust_telno_home, cust_email, cust_discount, cust_telno_mobile,
cust_title, cust_nodeposit, cust_deposit_requested, cust_nosms
from vwcustomer where cust_no = {cust_no}"""

        self.load_by_sql(sql)

        log.debug(f'Loaded customer {cust_no}')


class Customer:
    """Representing a PetAdmin Customer"""

    def __init__(self, cust_no):
        self.no = cust_no
        self.pets = []
        self.surname = ''
        self.forename = ''
        self.addr1 = ''
        self.addr2 = ''
        self.addr3 = ''
        self.postcode = ''
        self.telno_home = ''
        self.email = ''
        self.discount = 0.0
        self.telno_mobile = ''
        self.title = ''
        self.nodeposit = 0
        self.deposit_requested = 0
        self.notes = ''

    def add_pet(self, pet):
        self.pets.append(pet)

    def display_name(self):
        if self.title == '':
            display_name = ''
        else:
            display_name = self.title + ' '

        if self.forename != '':
            display_name += ' ' + self.forename

        if display_name != '':
            display_name += ' '

        display_name += self.surname

        return display_name

    def full_address(self):
        full_address = self.display_name()
        if self.addr1 != '':
            full_address += '\n' + self.addr1
        if self.addr2 != '':
            full_address += '\n' + self.addr2
        if self.postcode != '':
            full_address += '\n' + self.postcode

        return full_address

    def write(self, env):
        sql = f"""execute pcreate_customer '{self.surname}', '{self.forename}',
            '{self.addr1}', '{self.addr3}', '{self.postcode}',
            '{self.telno_home}', '{self.telno_mobile}', '{self.email}',
            '{self.notes}"""

        env.execute(sql)


class Breeds:
    """Representing a collection of breeds"""

    def __init__(self, env):
        self.breeds = {}
        self.env = env
        self.loaded = False

    def get(self, breed_no):
        if breed_no in self.breeds:
            return self.breeds[breed_no]
        else:
            return None

    def load(self, force=False):
        if self.loaded and not force:
            return

        log.debug('Loading Breeds')

        cursor = self.env.get_cursor()
        sql = 'select breed_no, breed_desc, spec_desc, billcat_desc from vwbreed'

        cursor.execute(sql)
        for row in cursor:
            breed_no = row[0]
            breed = Breed(breed_no)
            self.breeds[breed_no] = breed
            breed.desc = row[1]
            breed.spec = row[2]
            breed.bill_category = row[3]

        self.loaded = True


class Breed:
    """Representing a particular breed"""

    def __init__(self, breed_no):
        self.no = breed_no
        self.desc = ''
        self.spec = ''
        self.bill_category = ''

    def __str__(self):
        return self.desc


class Pets:
    """Representing a collection of Pets"""

    def __init__(self, env, customers=None, breeds=None):
        self.pets = {}
        self.env = env
        self.loaded = False
        self.customers = customers
        self.breeds = breeds

    def get(self, pet_no):
        if pet_no in self.pets:
            return self.pets[pet_no]
        else:
            return None

    def load_by_sql(self, sql):
        cursor = self.env.get_cursor()

        cursor.execute(sql)
        for row in cursor:
            pet_no = row[0]
            pet = Pet(pet_no)
            cust_no = row[1]
            if self.customers is not None:
                customer = self.customers.get(cust_no)
                if not customer:
                    log.error(f'Missing customer for pet #{pet_no}')
                    next()
                pet.customer = customer
                customer.add_pet(pet)
            pet.name = row[2]
            breed_no = row[3]
            if self.breeds is not None:
                breed = self.breeds.get(breed_no)
                if not breed:
                    log.error(f'Missing breed for pet #{pet_no}')
                    next()
            pet.breed = breed
            pet.spec = row[4]
            pet.dob = row[5]
            pet.sex = row[6]
            pet.vacc_status = row[7]
            self.pets[pet_no] = pet

    def load_for_customer(self, cust_no):
        if self.loaded:
            return

        log.debug(f'Loading Pets for customer #{cust_no}')

        if self.customers is not None and cust_no not in self.customers.customers:
            self.customers.load_one(cust_no)
        if self.breeds is not None:
            self.breeds.load()

        sql = f"""
select pet_no, cust_no, pet_name, breed_no, spec_desc, pet_dob, pet_sex,
pet_vacc_status from vwpet where cust_no = {cust_no}"""
        self.load_by_sql(sql)

        log.debug('Loaded %d pets', len(self.pets))
        self.loaded = True
        

    def load(self, force=False):
        if self.loaded and not force:
            return

        log.debug('Loading Pets')
        if self.customers is not None:
            self.customers.load()
        if self.breeds is not None:
            self.breeds.load()

        sql = """select pet_no, cust_no, pet_name, breed_no, spec_desc, pet_dob,
pet_sex, pet_vacc_status from vwpet"""
        self.load_by_sql(sql)

        log.debug(f'Loaded {len(self.pets)} pets')
        self.loaded = True


class Pet:
    """Reoresenting a PetAdmin Pet"""

    def __init__(self, pet_no):
        self.no = pet_no
        self.name = ''
        self.customer = None
        self.breed = None
        self.sex = ''
        self.spec = ''
        self.dob = datetime.date.today()

    def __str__(self):
        return self.name


class Services:
    """Representing a collection of PetAdmin services"""

    def __init__(self, env):
        self.env = env
        self.services = {}
        self.loaded = False

    def get(self, srv_no):
        if srv_no in self.services:
            return self.services[srv_no]
        else:
            return None

    def load(self, force=False):
        if self.loaded and not force:
            return

        sql = 'Select srv_no, srv_desc, srv_code from vwservice'
        cursor = self.env.get_cursor()
        cursor.execute(sql)

        for row in cursor:
            srv_no = row[0]
            service = Service(srv_no, row[1], row[2])
            self.services[srv_no] = service

        self.loaded = True


class Service:
    """Representing a PetAdmin service"""

    def __init__(self, srv_no, desc, code):
        self.srv_no = srv_no
        self.code = code
        self.desc = desc


class Bookings:
    """Representing a collection of Booking objects
    """

    def __init__(self, env, customers, pets, services):
        self.bookings = {}
        self.by_start_date = {}
        self.env = env
        self.loaded = False
        self.customers = customers
        self.pets = pets
        self.services = services

    def get(self, bk_no):
        if bk_no in self.bookings:
            return self.bookings[bk_no]
        else:
            return None

    def get_by_start_date(self, start_date):
        self.load()
        if start_date in self.by_start_date:
            return self.by_start_date[start_date]
        
        return []
        
    def load_by_sql(self, sql_booking, sql_bookingitem, sql_invitem,
            sql_invextra, sql_payment):
        cursor = self.env.get_cursor()
        cursor.execute(sql_booking)

        for row in cursor:
            bk_no = row[0]
            booking = Booking(bk_no)
            cust_no = row[1]
            booking.customer = self.customers.get(cust_no)
            booking.create_date = row[2]
            booking.start_date = row[3]
            booking.end_date = row[4]
            booking.gross_amt = row[5]
            booking.paid_amt = row[6]
            booking.status = row[7]
            booking.peak = row[8]
            booking.deluxe = row[9]
            booking.skip = row[10]
            booking.pickup = row[11]
            self.bookings[bk_no] = booking
            sdate = booking.start_date.date()
            if booking.status == '' or booking.status == 'V':
                if sdate in self.by_start_date:
                    self.by_start_date[sdate].append(booking)
                else:
                    self.by_start_date[sdate] = [booking]

        cursor.execute(sql_bookingitem)

        for row in cursor:
            booking = self.get(row[0])
            pet = self.pets.get(row[1])
            if not booking:
                pass
            else:
                booking.pets.append(pet)

        cursor.execute(sql_invitem)

        for row in cursor:
            booking = self.get(row[0])
            if booking:
                pet = self.pets.get(row[1])
                service = self.services.get(row[2])
                inv_item = InventoryItem(pet, service, row[3], row[4])
                booking.inv_items.append(inv_item)

        cursor.execute(sql_invextra)

        for row in cursor:
            booking = self.get(row[0])
            if booking:
                desc = row[1]
                unit_price = row[2]
                quantity = row[3]
                extra_item = ExtraItem(desc, unit_price, quantity)
                booking.extra_items.append(extra_item)

        cursor.execute(sql_payment)

        for row in cursor:
            booking = self.get(row[0])
            pay_date = row[1]
            amount = row[2]
            pay_type = row[3]
            payment = Payment(pay_date, amount, pay_type)
            booking.payments.append(payment)


    def load(self, force=False):
        if self.loaded and not force:
            return

        log.debug('Loading Bookings')

        sql_booking = """
Select bk_no, bk_cust_no, bk_create_date, bk_start_datetime, bk_end_datetime,
bk_gross_amt, bk_paid_amt, bk_status, bk_peak, bk_deluxe, bk_skip_confirm,
bk_pickup_no from vwbooking"""
        sql_bookingitem = """
Select bi_bk_no, bi_pet_no from vwbookingitem_simple"""
        sql_invitem = """
Select ii_bk_no, ii_pet_no, ii_srv_no, ii_quantity, ii_rate from vwinvitem"""
        sql_invextra = """
Select ie_bk_no, ie_desc, ie_unit_price, ie_quantity from vwinvextra"""
        sql_payment = """
Select pay_bk_no, pay_date, pay_amount, pay_type from vwpayment_simple"""

        self.load_by_sql(sql_booking, sql_bookingitem, sql_invitem, sql_invextra,
            sql_payment)

        log.debug(f'Loaded {len(self.bookings)} bookings')
        self.loaded = True


    def load_for_customer(self, cust_no):
        if self.loaded:
            return

        log.debug(f'Loading Bookings for customer #{cust_no}')
        sql_booking = f"""
Select bk_no, bk_cust_no, bk_create_date, bk_start_datetime, bk_end_datetime,
bk_gross_amt, bk_paid_amt, bk_status, bk_peak, bk_deluxe, bk_skip_confirm,
bk_pickup_no from vwbooking
where bk_cust_no = {cust_no}"""
        sql_bookingitem = f"""
Select bi_bk_no, bi_pet_no
from vwbookingitem_simple
where bi_cust_no = {cust_no}"""
        sql_invitem = f"""
Select ii_bk_no, ii_pet_no, ii_srv_no, ii_quantity, ii_rate
from vwinvitem where ii_cust_no = {cust_no}"""
        sql_invextra = f"""
Select ie_bk_no, ie_desc, ie_unit_price, ie_quantity
from vwinvextra
where ie_cust_no = {cust_no}"""
        sql_payment = f"""
Select pay_bk_no, pay_date, pay_amount, pay_type
from vwpayment_simple where pay_cust_no = {cust_no}"""

        self.load_by_sql(sql_booking, sql_bookingitem, sql_invitem, sql_invextra,
            sql_payment)

        log.debug(f'Loaded bookings for customer #{cust_no}')
        self.loaded = True


class Payment:
    def __init__(self, pay_date, amount, pay_type):
        self.pay_date = pay_date
        self.amount = amount
        self.type = pay_type


class ExtraItem:
    def __init__(self, desc, unit_price, quantity):
        self.desc = desc
        self.unit_price = unit_price
        self.quantity = quantity


class InventoryItem:
    def __init__(self, pet, service, quantity, rate):
        self.pet = pet
        self.service = service
        self.quantity = quantity
        self.rate = rate


class Booking:
    """Representing a PetAdmin Booking"""

    def __init__(self, bk_no):
        self.no = bk_no
        self.customer = None
        self.pets = []
        self.create_date = None
        self.start_date = None
        self.end_date = None
        self.status = ''
        self.skip = 0
        self.gross_amt = decimal.Decimal("0.0")
        self.paid_amt = decimal.Decimal("0.0")
        self.inv_items = []
        self.extra_items = []
        self.payments = []
        self.peak = 0
        self.deluxe = 0
        self.skip = 0

    def pet_names(self):
        if len(self.pets) == 1:
            return self.pets[0].name
        return ', '.join(map(lambda p: p.name, self.pets[0:-1])) + \
            ' and ' + self.pets[-1].name

    def add_payment(self, payment):
        self.payments.append(payment)

    def outstanding_amt(self):
        return self.gross_amt - self.paid_amt


class Runs:
    """
    Representing the collection of all runs in the kennels
    """

    def __init__(self, env, bookings, pets):
        self.runs = {}
        self.env = env
        self.runs_by_type = {}
        self.bookings = bookings
        self.pets = pets
        self.potential_vacancies = {}
        self.vacancies = {}
        self.min_date = datetime.date(2099, 12, 31)
        self.max_date = datetime.date(1970, 1, 1)
        self.loaded = False
        
    def load(self, force=False):
        if self.loaded and not force:
            return

        sql = "select run_no, run_code, spec_desc, rt_desc from vwrun"
        cursor = self.env.get_cursor()
        cursor.execute(sql)

        for row in cursor:
            run = Run()
            run.no = row[0]
            run.code = row[1]
            run.spec = row[2]
            run.type = row[3]
            self.runs[run.no] = run
            if run.spec not in self.runs_by_type:
                self.runs_by_type[run.spec] = {}

            if run.type not in self.runs_by_type[run.spec]:
                self.runs_by_type[run.spec][run.type] = []

            self.runs_by_type[run.spec][run.type].append(run)
            if not (run.spec, run.type) in self.potential_vacancies:
                self.potential_vacancies[(run.spec, run.type)] = 0
            self.potential_vacancies[(run.spec, run.type)] += 1

        sql = """
select ro_run_no, ro_pet_no, ro_date, ro_bk_no, ro_type from vwrunoccupancy"""
        cursor.execute(sql)

        for row in cursor:
            run = self.runs[row[0]]
            pet = self.pets.get(row[1])
            ro_date = row[2].date()
            booking = self.bookings.get(row[3])
            ro_type = row[4]
            run.add_occupancy(booking, pet, ro_date, ro_type)
            if ro_date < self.min_date:
                self.min_date = ro_date
            if ro_date > self.max_date:
                self.max_date = ro_date

        ro_date = self.min_date
        one_day = datetime.timedelta(days=1)
        while ro_date <= self.max_date:
            self.vacancies[ro_date] = {}
            for spec in self.runs_by_type.keys():
                for run_type in self.runs_by_type[spec].keys():
                    self.vacancies[ro_date][(spec, run_type)] = \
                        self.potential_vacancies[(spec, run_type)]
                    for run in self.runs_by_type[spec][run_type]:
                        if ro_date in run.occupancy:
                            self.vacancies[ro_date][(spec, run_type)] -= 1
            ro_date += one_day

        self.loaded = True

    def check_availability(self, from_date, to_date, spec, run_type, run_count=1):
        """
        Check to see whether we have availability in a given type of run.
        A run is considered available only if no pet is assigned to each at
        any time during the day.
        Thus the test may fail while there is still room to accommodate leavers
        and arrivers in the same run
        :param from_date:   first date to be checked, typically bk_start_date
        :param to_date:     last date to be checked, typically bk_end_date
        :param spec:        species, 'Cat' or 'Dog'
        :param run_type:    run type, e.g. 'standard', 'double' or 'deluxe'
                            for dogs
        :param run_count: Number of runs required (default to 1)
        :return:
        """

        one_day = datetime.timedelta(days=1)
        ro_date = from_date
        while ro_date <= to_date:
            if self.vacancies[ro_date][[spec, run_type]] < run_count:
                return False
            ro_date += one_day

        return True

    def allocate_booking(self, booking, run_type=None, pets=None, start_date=None,
        stay_length=0):
        """
        :param booking: booking to be allocated into runs
        :param run_type: type of run to be used for dogs.
            All cats are assumed to use standard run.
        :param pets: a list of pets to be allocated.
            If None, all pets of each spec are co-habiting
        :param start_date: first date to be allocated.
            defaults to booking.start_date
        :param stay_length: number of days to be allocated.
            defaults to length of booking
        :return: True for success, False for failure
        """

        if pets is None:
            pets = booking.pets

        for spec in ['Cat', 'Dog']:
            spec_pets = filter(lambda p: p.spec == spec, pets)
            if spec_pets:
                if spec == 'Cat' or run_type is None:
                    spec_run_type = 'Standard'
                else:
                    spec_run_type = run_type

                if not stay_length:
                    stay_length = (booking.end_date - booking.start_date).days + 1

                if not start_date:
                    start_date = booking.start_date

                run = max(self.runs_by_type[spec][spec_run_type],
                          key=lambda r: r.free_length(start_date, stay_length))

                move_list = []
                run.add_occupancy_range(booking, spec_pets, booking.start_date,
                    stay_length, move_list)
                while move_list:
                    to_move = move_list.pop(0)
                    self.allocate_booking(to_move[0][0], run.run_type,
                        to_move[0][1], to_move[1], to_move[2])


class Run:
    """
    Representing a dog kennel or cat pen
    """

    def __init__(self):
        self.no = -1
        self.code = ''
        self.occupancy = {}
        self.spec = ''
        self.type = ''

    def add_occupancy(self, booking, pet, ro_date, ro_type=None):
        if ro_date not in self.occupancy:
            self.occupancy[ro_date] = {}

        if booking.no not in self.occupancy[ro_date]:
            self.occupancy[ro_date][booking.no] = [booking, [pet], ro_type]
        else:
            self.occupancy[ro_date][booking.no][1].append(pet)

    def free_length(self, ro_date, ro_length):
        if ro_date in self.occupancy:
            return 0

        i = 0

        for i in range(ro_length):
            if ro_date + datetime.timedelta(days=i) in self.occupancy:
                break

        return i

    def same_length(self, current_date, bk_no):
        current_set = self.occupancy[current_date][bk_no]
        i = 1
        while bk_no in self.occupancy[current_date + datetime.timedelta(days=i)]\
             and self.occupancy[current_date + datetime.timedelta(days=i)][1] ==\
              current_set[1]:
            i += 1

        return i

    def clear_run(self, start_date, bk_no, stay_length):
        for i in range(stay_length):
            del self.occupancy[start_date + datetime.timedelta(days=i)][bk_no]

    def add_occupancy_range(self, booking, pets, from_date, day_count, reject_list):
        for i in range(day_count):
            current_date = from_date + datetime.timedelta(days=i)
            if current_date in self.occupancy:
                for bk_no in self.occupancy[current_date]:
                    stay_length = self.same_length(current_date, bk_no)
                    reject_list.append((self.occupancy[current_date], \
                    current_date, stay_length))
                    self.clear_run(current_date, bk_no, stay_length)
            for pet in pets:
                self.add_occupancy(booking, pet, current_date)
