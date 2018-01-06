import fbchat
from settings import FACEBOOK_USER, FACEBOOK_PASSWORD
import logging
from petadmin import Environment
from os import getenv
import argparse


log = logging.getLogger(__name__)
env = Environment()

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

env.context = 'confirm'

env.is_test = ENVIRONMENT in ('dev', 'qa')
env.configure_logger(log, ENVIRONMENT == 'dev')


class Employees:
    def __init__(self, env):
        self.employees = {}
        self.employees_by_forename = {}
        self.loaded = False
        self.env = env

    def get(self, emp_no):
        if emp_no in self.employees:
            return self.employees[emp_no]
        else:
            return None

    def get_by_forename(self, forename):
        if forename in self.employees_by_forename:
            return self.employees_by_forename[forename]
        else:
            return None

    def load(self, force=False):
        if self.loaded and not force:
            return

        log.debug('Loading Employees')
        sql = """Select emp_no, emp_forename, emp_surname, emp_facebook from vwemployee where emp_iscurrent = 1"""
        cursor = self.env.get_cursor()
        cursor.execute(sql)

        for row in cursor:
            emp_no = row[0]
            employee = Employee(emp_no, row[1], row[2], row[3])
            self.employees[emp_no] = employee
            self.employees_by_forename[row[1]] = employee

        self.loaded = True


class Employee:
    def __init__(self, no, forename, surname, facebook):
        self.no = no
        self.forename = forename
        self.surname = surname
        self.facebook = facebook


class Facebook:
    def __init__(self):
        self.client = None

    def login(self):
        if not self.client:
            self.client = fbchat.Client(FACEBOOK_USER, FACEBOOK_PASSWORD)

    def send(self, msg, uid):
        self.login()

        if ENVIRONMENT != 'prod':
            pass
        else:
            sent = self.client.send(uid, msg)

        if sent:
            log.info('Successfully sent message to %s', uid)
        else:
            log.warning('Failed to send message to %s', uid)

    def send_to_employee(self, msg, employee):
        addr = employee.facebook
        if addr:
            self.send(msg, addr)

    def send_to_all_employees(self, msg):
        for employee in Employees.employees.values():
            self.send_to_employee(msg, employee)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-msg', help='Message', action='store')
    parser.add_argument('-to', help='Employee forename', action='store')
    parser.add_argument('-all', action='store_true', help='Send message to all employees')

    args = parser.parse_args()

    employees = Employees(env)
    employees.load()

    fb = Facebook()

    if args.all:
        fb.send_to_all_employees(args.msg)
    else:
        to = args.to
        employee = employees.get_by_forename(to)
        if employee:
            fb.send_to_employee(args.msg, employee)


if __name__ == '__main__':
    main()
