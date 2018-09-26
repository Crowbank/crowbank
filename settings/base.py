import sys

EMAIL_HOST = 'cp165172.hpdns.net'
# EMAIL_USER = 'confirmations@crowbank.co.uk'
EMAIL_USER = 'info@crowbank.co.uk'
EMAIL_PWD = 'Crowb@nk454!'

# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_USER = 'crowbank.partners@gmail.com'
# EMAIL_PWD = 'fackfdtiecquhggp'
EMAIL_BCC = 'crowbank.partners@gmail.com'
EMAIL_LOGS = 'crowbank.partners@gmail.com'
EMAIL_REPLYTO = 'info@crowbank.co.uk'

if sys.platform == 'win32':
    IMAGE_FOLDER = 'C:\Python27\Lib\Site-packages\crowbank\img'
    CONFIRMATIONS_FOLDER = 'D:\Dropbox\Kennels\Confirmations'
else:
    IMAGE_FOLDER = '/usr/lib/python2.7/site-packages/crowbank/img'
    CONFIRMATIONS_FOLDER = '/dropbox/Kennels/Confirmations'
CROWBANK_ADDRESSES = ['info@crowbank.co.uk', 'crowbank.partners@gmail.com', 'eyehudai@gmail.com']

FACEBOOK_USER = 'crowbank.partners@gmail.com'
FACEBOOK_PASSWORD = 'Crowbank454'