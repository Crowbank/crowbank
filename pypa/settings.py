import sys


def get_settings(env='prod'):
    settings = {
        'EMAIL_HOST': 'cp165172.hpdns.net',
        'EMAIL_USER': 'info@crowbank.co.uk',
        'EMAIL_PWD': 'Crowbank454!',
        'EMAIL_BCC': 'crowbank.partners@gmail.com',
        'EMAIL_LOGS': 'crowbank.partners@gmail.com',
        'EMAIL_REPLYTO': 'info@crowbank.co.uk',
        'CROWBANK_ADDRESSES': [
            'info@crowbank.co.uk',
            'crowbank.partners@gmail.com',
            'eyehudai@gmail.com'],
        'FACEBOOK_USER': 'crowbank.partners@gmail.com',
        'FACEBOOK_PASSWORD': 'Crowbank454',
        'TEXTMAGIC_USERNAME': 'eranyehudai',
        'TEXTMAGIC_TOKEN': 'xhT9jS11ezxRO2OAtcK8ESWr9OMfcE'
    }

    if sys.platform == 'win32':
#            'C:/Program Files/Python37/Lib/Site-packages/crowbank/img'
        settings['IMAGE_FOLDER'] = 'Z:/Website/crowbank-python/img'
        settings['VACC_FOLDER'] = 'K:/Vaccinations'
        if env == 'prod':
            settings['CONFIRMATIONS_FOLDER'] = 'K:/Confirmations'
        else:
            settings['CONFIRMATIONS_FOLDER'] = \
                'Z:/Website/crowbank-python/tests/confirmations'
    else:
        settings['IMAGE_FOLDER'] = \
            '/usr/lib/python3.7/site-packages/crowbank/img'
        settings['CONFIRMATIONS_FOLDER'] = \
            '/dropbox/Kennels/Confirmations'
        settings['VACC_FOLDER'] = '/dropbox/Kennels/Vaccinations'

    if env == 'prod':
        if sys.platform == 'win32':
            settings['LOG_FILE'] = 'Z:/Website/logs/crowbank.log'
        else:
            settings['LOG_FILE'] = '/dropbox/Website/crowbank.log'

        settings['DB_SERVER'] = 'HP-SERVER\\SQLEXPRESS'
        settings['DB_USER'] = 'PA'
        settings['DB_PWD'] = 'petadmin'
        settings['DB_DATABASE'] = 'crowbank'
    else:
        if sys.platform == 'win32':
            settings['LOG_FILE'] = 'Z:/Website/logs/crowbank_dev.log'
        else:
            settings['LOG_FILE'] = \
                '/usr/lib/site-packages/crowbank/logs/dev.log'

        settings['DB_SERVER'] = 'HP-SERVER\\SQLEXPRESS_dev'
        settings['DB_USER'] = 'PA'
        settings['DB_PWD'] = 'petadmin'
        settings['DB_DATABASE'] = 'crowbank'

    return settings
