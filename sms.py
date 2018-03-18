from textmagic.rest import TextmagicRestClient
from petadmin import PetAdmin, Environment
import re
import datetime
import argparse
import logging
from os import getenv


log = logging.getLogger(__name__)
env = Environment()

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

env.context = 'sms'

env.is_test = ENVIRONMENT in ('dev', 'qa')
env.configure_logger(log, ENVIRONMENT == 'dev')

log.info('Running sms with ENVIRONMENT=%s', ENVIRONMENT)

client = TextmagicRestClient()

def pet_name_combine(pets):
    names = map(lambda p: p.name, pets)
    if len(names) == 1:
        return names[0]
    
    comb = ', '.join(names[:-1])
    comb += ' and ' + names[-1]
    return comb

def send_sms(pa, booking, test):
    
    if booking.start_date.date() == datetime.date.today() + datetime.timedelta(days=1):
        date_string = 'tomorrow'
    else:
        date_string = 'on ' + booking.start_date.strftime("%A %d/%m/%Y")
    
    if (booking.pickup != -1):
        vacc_msg = 'You do not need to prepare vaccination cards this time.\n'
    else:
        vacc_msg = 'You do not need to bring vaccination cards this time.\n'
    
    unconfirmed_pets = []
    for pet in booking.pets:
        if pet.vacc_status == 'Valid':
            continue
        
        unconfirmed_pets.append(pet)

    if unconfirmed_pets:
        if len(unconfirmed_pets) > 1:
            card_msg = 'vaccination cards'
        else:
            card_msg = 'a vaccination card'
            
        if (booking.pickup != -1):
            vacc_msg = 'You need to have %s for %s ready.\n' % (card_msg, pet_name_combine(unconfirmed_pets))
        else:
            vacc_msg = 'You need to bring %s for %s.\n' % (card_msg, pet_name_combine(unconfirmed_pets))
        
    if (booking.pickup != -1):
        msg = "We are due to pick up %s for Crowbank %s at %s.\n" % \
            (booking.pet_names(), date_string, booking.start_date.strftime("%H:%M"))
    else:
        msg = "You are due to bring in %s to Crowbank %s at %s.\n" % \
            (booking.pet_names(), date_string, booking.start_date.strftime("%H:%M"))
            
    msg += vacc_msg
    msg += "Call us at 01236 729454 or reply to this message with any changes"
    
    phone = booking.customer.telno_mobile.replace(' ', '')
    phone = re.sub('^0', '44', phone)
    
    if test:
        msg += '\n[Testing - would have been sent to %s]' % phone
        client.messages.create(phones="447590507946", text=msg)
        log_msg = 'Test Sent: %s\nTo: %s' % (msg, phone)    

    else:
        log_msg = 'Sent: %s\nTo: %s' % (msg, phone)
        client.messages.create(phones=phone, text=msg)
    
    log.info(log_msg)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-booking', nargs='*', action='store', type=int, help='Booking number(s)')
    parser.add_argument('-date', action='store', help='The date for which messages are to be sent [YYYYMMDD]')
    parser.add_argument('-test', action='store_true', help='Send all messages to Eran')

    args = parser.parse_args()

    if args.date:
        start_date = datetime.strptime(args.date, '%Y%m%d') 
    else:
        start_date = datetime.date.today() + datetime.timedelta(days=1)
    
    test = args.test
    
    pa = PetAdmin(env)
    pa.load()

    if args.booking:
        bookings = []
        for bk_no in args.booking:
            bookings.append(pa.bookings.get(bk_no))
    else:
        bookings = pa.bookings.get_by_start_date(start_date)
    
    for booking in bookings:
        customer = booking.customer
        if customer.telno_mobile and not customer.nosms:
            send_sms(pa, booking, test)
        else:
            if customer.nosms:
                log.warning('Skipping booking %d - customer marked as no sms' % booking.bk_no)
            else:
                log.warning('Skipping booking %d - no mobile number' % booking.bk_no)

    env.close()


if __name__ == '__main__':
    main()
