import sys

EMAIL_HOST = 'cp165172.hpdns.net'
# EMAIL_USER = 'confirmations@crowbank.co.uk'
EMAIL_USER = 'info@crowbank.co.uk'
EMAIL_PWD = 'Crowbank454!'

# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_USER = 'crowbank.partners@gmail.com'
# EMAIL_PWD = 'fackfdtiecquhggp'
EMAIL_BCC = 'crowbank.partners@gmail.com'
EMAIL_LOGS = 'crowbank.partners@gmail.com'
EMAIL_REPLYTO = 'info@crowbank.co.uk'

if sys.platform == 'win32':
    IMAGE_FOLDER = 'C:\Program Files\Python37\Lib\Site-packages\crowbank\img'
    CONFIRMATIONS_FOLDER = 'D:\Dropbox\Kennels\Confirmations'
    VACC_FOLDER = 'K:\Vaccinations'
else:
    IMAGE_FOLDER = '/usr/lib/python3.7/site-packages/crowbank/img'
    CONFIRMATIONS_FOLDER = '/dropbox/Kennels/Confirmations'
    VACC_FOLDER = '/dropbox/Kennels/Vaccinations'
CROWBANK_ADDRESSES = ['info@crowbank.co.uk', 'crowbank.partners@gmail.com', 'eyehudai@gmail.com']

FACEBOOK_USER = 'crowbank.partners@gmail.com'
FACEBOOK_PASSWORD = 'Crowbank454'