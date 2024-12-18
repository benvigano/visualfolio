import os
import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


# Variables
# -----------------------------------------------------------------------------
ENV_FILE = Path('/etc/visualfolio_env')
REQUIRED_VARIABLES = [
    "VISUALFOLIO_SECRET_KEY",
    "VISUALFOLIO_DEBUG",
    "VISUALFOLIO_MODE",
    "VISUALFOLIO_ALLOWED_HOSTS",
]

if ENV_FILE.exists():
    with ENV_FILE.open('r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            # Setdefault doesn't overwrite vars already set in the environment
            os.environ.setdefault(key, value)

SECRET_KEY = os.environ.get("VISUALFOLIO_SECRET_KEY")
DEBUG = os.environ.get("VISUALFOLIO_DEBUG").lower() == "true"
MODE = os.environ.get("VISUALFOLIO_MODE")
ALLOWED_HOSTS = os.environ.get("VISUALFOLIO_ALLOWED_HOSTS").split(",")


# Demo
# -----------------------------------------------------------------------------
if MODE == 'demo':
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    DEMO_ACCOUNT_CUTOFF = datetime.timedelta(hours=3)
else:
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# Customization
# -----------------------------------------------------------------------------
BASE_CURRENCY = {"code": "EUR", "symbol": "€"}
DEFAULT_THEME = "light"


# Application
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    'main.apps.MainConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'main.middleware.DemoUserExistenceMiddleware',
    'main.middleware.ThemeMiddleware',
]
ROOT_URLCONF = 'visualfolio.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.context_processors.current_path',
            ],
        },
    },
]
WSGI_APPLICATION = 'visualfolio.wsgi.application'


# Database
# -----------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = 'main.CustomUser'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files
# -----------------------------------------------------------------------------
STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_ROOT = BASE_DIR / "staticfiles"

# Security
# -----------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
REFERRER_POLICY = 'strict-origin-when-cross-origin'

if DEBUG:
    # Development settings (http)
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
else:
    # Production settings (https)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# Logging
# -----------------------------------------------------------------------------
# Ensure the logs directory exists
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
STATIC_ROOT.mkdir(exist_ok=True)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console_debug': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'file_info': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'visualfolio_info.log',
            'formatter': 'verbose',
            'level': 'INFO',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
        },
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'visualfolio_error.log',
            'formatter': 'verbose',
            'level': 'ERROR',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'visualfolio': {
            'handlers': ['console_debug', 'file_info', 'file_error'] if DEBUG else ['file_info', 'file_error'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'visualfolio_scheduled_tasks': {
            'handlers': ['console_debug', 'file_info', 'file_error'] if DEBUG else ['file_info', 'file_error'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
