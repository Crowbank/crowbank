from pickle import load
from os import listdir, path, rename
from petadmin import Environment
import logging

class LocalMessage():
    def __init__(self, filename):
        self.msg = load(open(filename))


class ActionCenter():
    INBOX = 'inbox'
    ARCHIVE = path.join(INBOX, 'archive')

    def __init__(self):
        self.registered_actions = {}

    def register(self, action, method):
        self.registered_actions[action] = method

    def act(self, msg):
        if msg.action in self.registered_actions:
            self.registered_actions[msg.action](msg.context)

    def act_all(self):
        files = listdir(ActionCenter.INBOX)
        files.sort()
        for f in files:
            fname = path.join(ActionCenter.INBOX, f)
            lm = LocalMessage(fname)
            self.act(lm.msg)
            rename(fname, path.join(ActionCenter.ARCHIVE, f))


env = Environment()
log = logging.getLogger(__name__)
ac = ActionCenter()


def deposit_request(context):
    bk_no = context['bk_no']
    deposit_amount = context['deposit_amount']

    sql = 'Execute pdeposit_request %d, %f' % (bk_no, deposit_amount)
    env.execute(sql)

ac.register('deposit_request', deposit_request)


def confirmation_file(context):
    file_name = context['file_name']
    body = context['body']

    f = open(file_name, 'w')
    f.write(body)

ac.register('confirmation_file', confirmation_file)


def insert_confaction(context):
    conf_no = context['conf_no']
    bk_no = context['bk_no']
    subject = context['subject']
    file_name = context['file_name']

    sql = "Execute pinsert_confaction %d, %d, '', '%s', '%s'" % (conf_no, bk_no, subject, file_name)
    env.execute(sql)

ac.register('insert_confaction', insert_confaction)


def main():
    ac.act_all()


if __name__ == '__main__':
    main()
