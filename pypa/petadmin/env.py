import sys
if sys.platform == 'win32':
    import pymssql
if sys.platform == 'cygwin':
    import pyodbc
import smtplib
import logging
import logging.handlers
import re
from os import getenv

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime

log = logging.getLogger(__name__)

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

from .settings import EMAIL_HOST, EMAIL_USER, EMAIL_PWD, EMAIL_BCC, EMAIL_LOGS,\
    EMAIL_REPLYTO, CROWBANK_ADDRESSES, LOG_FILE, DB_SERVER, DB_USER, DB_PWD,\
    DB_DATABASE

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
Execute plog '{msg.replace("'", "''")}', '{levelname}', '{self.env.context}',
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
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        msg['Message-Id'] = f'{timestamp}@crowbank.co.uk'

        part1 = MIMEText(alt_body, 'plain')
        part2 = MIMEText(send_body, 'html')

        msg.attach(part1)
        msg.attach(part2)

        try:
            server = self.get_smtp_server()
            server.sendmail(self.email_user, [send_to], msg.as_string())
        except smtplib.SMTPServerDisconnected:
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
        except smtplib.SMTPServerDisconnected:
            self.smtp_server.connect()
            self.smtp_server.sendmail(self.email_user, target, msg)

    def close(self):
        if self.connection:
            self.connection.close()
        if self.smtp_handler:
            self.smtp_handler.flush()
