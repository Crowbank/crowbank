from petadmin import Environment
import logging
import sys
from os import getenv, path

log = logging.getLogger(__name__)
env = Environment()

ENVIRONMENT = getenv("DJANGO_ENVIRONMENT")
if not ENVIRONMENT:
    ENVIRONMENT = 'prod'

env.context = 'log_test'

env.is_test = ENVIRONMENT in ('dev', 'qa')
env.configure_logger(log, ENVIRONMENT == 'dev')
env.env_type = ENVIRONMENT

log.info('Running log_test with ENVIRONMENT=%s', ENVIRONMENT)
log.error('This is a purposeful error message')
env.close()
