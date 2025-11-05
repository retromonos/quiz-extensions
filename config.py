import os

# Canvas API URL (e.g. 'http://example.com/api/v1/')
API_URL = os.environ.get("API_URL")

API_KEY = os.environ.get("API_KEY")

# A list of domains that are allowed to use the tool.
# (e.g. ['example.com', 'example.edu'])
ALLOWED_CANVAS_DOMAINS = os.environ.get("ALLOWED_CANVAS_DOMAINS").replace(" ", "").split(",")

# The maximum amount of objects the Canvas API will return per page (usually 100)
MAX_PER_PAGE = int(os.environ.get("MAX_PER_PAGE"))

# A secret key used by Flask for signing. KEEP THIS SECRET!
# (e.g. 'Ro0ibrkb4Z4bZmz1f5g1+/16K19GH/pa')
SECRET_KEY = os.environ.get("SECRET_KEY")

LTI_TOOL_ID = os.environ.get("LTI_TOOL_ID") # A unique ID for the tool

# URI for database. (e.g. 'mysql://root:root@localhost/quiz_extensions')
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = int(os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")) == 1

GOOGLE_ANALYTICS = os.environ.get("GOOGLE_ANALYTICS")  # The Google Analytics ID to use.

# URL for the redis server (e.g. 'redis://localhost:6379')
#REDIS_URL = "redis://quiz_redis:6379"
REDIS_URL = os.environ.get("REDIS_URL")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] {%(filename)s:%(lineno)d} %(message)s"
        },
        "bare": {"format": "%(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/quiz_ext.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "app": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": True}
    },
}

TESTING_API_URL = os.environ.get("TESTING_API_URL")  # Used only to run tests


CONSUMER_KEY = os.environ.get("CONSUMER_KEY", "key")
SHARED_SECRET = os.environ.get("SHARED_SECRET", "secret")

# Configuration for LTI
PYLTI_CONFIG = {
    "consumers": {
        CONSUMER_KEY: {"secret": SHARED_SECRET}
        # Feel free to add more key/secret pairs for other consumers.
    },
    "roles": {
        # Maps values sent in the lti launch value of "roles" to a group
        # Allows you to check LTI.is_role('staff') for your user
        "staff": [
            "urn:lti:instrole:ims/lis/Administrator",
            "Instructor",
            # 'ContentDeveloper',
            # 'urn:lti:role:ims/lis/TeachingAssistant'
        ]
    },
}

# Chrome 80 SameSite=None; Secure fix
SESSION_COOKIE_SECURE = int(os.environ.get("SESSION_COOKIE_SECURE")) == 1
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE")
