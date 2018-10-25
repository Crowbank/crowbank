import os
from .base import *

ENVIRONMENT = os.getenv("DJANGO_ENVIRONMENT")

if ENVIRONMENT == "prod":
    from .prod import *
elif ENVIRONMENT == "qa":
    from .qa import *
elif ENVIRONMENT == "dev":
    from .dev import *
else:
    from .prod import *

try:
    from .local import *
except ImportError:
    pass
