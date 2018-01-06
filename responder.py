import argparse
from petadmin import Environment
import requests
from time import sleep
from confirm import handle_remote_confirmation

import logging
import json

log = logging.getLogger(__name__)
env = Environment()

env.configure_logger(log)


def message_reflector(data):
    if 'requested_code' in data:
        requested_code = data['requested_code']
    else:
        requested_code = 0
    return requested_code, ''


HANDLERS = {
    'confirmation-sent': handle_remote_confirmation,
    'message-reflector': message_reflector
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-url', action='store', help='URL to use', default='http://www.crowbank.site/messaging/dispatch')
    parser.add_argument('-sleep', action='store', help='Sleep time (seconds)', default=10)

    args = parser.parse_args()
    url = args.url
    sleep_time = float(args.sleep)

    return_message = ''
    queue_length = 0

    log.info('Starting responder with sleep %f sec', sleep_time)

    while True:
        data = {}
        if return_message:
            data['message'] = return_message

        try:
            r = requests.post(url, data=data, headers=dict(Referer=url))
            if return_message:
                log.info('Successfully returned %s', return_message)
                return_message = ''
            txt = r.text
            if txt:
                try:
                    incoming_message = json.loads(txt)
                except Exception as e:
                    log.error('Failed decode message: %s', e.message)
                    continue
                message_type = incoming_message['type']
                message_no = incoming_message['no']
                message_payload = incoming_message['payload']
                queue_length = incoming_message['queue_length']
                message_data = json.loads(message_payload)
                log.info('Received message %d of type %s', message_no, message_type)
                if message_type == 'responder-control':
                    if 'sleep' in message_data:
                        sleep_time = float(message_data['sleep'])
                    if 'stop' in message_data:
                        break;
                    if 'simulate' in message_data:
                        return_message = json.dumps({'no': message_no, 'code': message_data['simulate'], 'msg': ''})
                else:
                    if message_type in HANDLERS:
                        handler = HANDLERS[message_type]
                        code, msg = handler(message_data)
                    else:
                        code = 0
                    return_message = json.dumps({'no': message_no, 'code': code, 'msg': msg})

            if not (queue_length or return_message):
                sleep_time = float(sleep_time)
                if sleep_time > 0:
                    sleep(sleep_time)
                else:
                    if sleep_time < 0:
                        break;
        except Exception as e:
            log.error('Failed to retrieve message: %s', e.message)


if __name__ == '__main__':
    main()
