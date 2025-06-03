import os
from pathlib import Path
from typing import Any, Optional, Sequence, TypedDict, Dict
import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent


class EnvVarConfig(TypedDict, total=False):
    required: bool
    default: Any
    coerce_type: type
    allowed_values: Sequence[Any]
    required_in_modes: Sequence[str]


def get_env_var(name: str, config: EnvVarConfig, current_mode: Optional[str] = None) -> Any:
    """
    Get an environment variable with validation and type coercion based on configuration.
    
    Args:
        name: Name of the environment variable
        config: Configuration dictionary containing validation rules
        current_mode: Current deployment mode for conditional requirements
    """
    value = os.environ.get(name)
    
    # Check if variable is required in current mode
    is_required = config.get('required', False)
    if not is_required and current_mode:
        required_in_modes = config.get('required_in_modes', [])
        is_required = current_mode in required_in_modes
    
    if value is None:
        if is_required:
            raise ValueError(f"Environment variable {name} is required in {current_mode or 'all'} mode(s) but not set.")
        return config.get('default')
    
    coerce_type = config.get('coerce_type')
    
    # Handle boolean type specially
    if coerce_type == bool:
        value = value.lower()
        if value not in ('true', 'false'):
            raise ValueError(f"Environment variable {name} must be 'true' or 'false', got '{value}'")
        return value == "true"
    
    # Handle other type coercion
    if coerce_type:
        try:
            value = coerce_type(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Environment variable {name} could not be converted to {coerce_type.__name__}: {e}")
    
    # Validate against allowed values if specified
    allowed_values = config.get('allowed_values')
    if allowed_values is not None and value not in allowed_values:
        allowed_str = ", ".join(str(v) for v in allowed_values)
        raise ValueError(f"Environment variable {name} must be one of: {allowed_str}, got '{value}'")
    
    return value


# Environment Variable Configuration
# -----------------------------------------------------------------------------
ENV_CONFIG: Dict[str, EnvVarConfig] = {
    "VISUALFOLIO_ENVIRONMENT": {
        "required": True,
        "allowed_values": ('local', 'cloud')
    },
    "DJANGO_SECRET_KEY": {
        "required": True
    },
    "DJANGO_DEBUG": {
        "required": True,
        "coerce_type": bool
    },
    "DJANGO_ALLOWED_HOSTS": {
        "required": True
    },
    "DJANGO_CSRF_TRUSTED_ORIGINS": {
        "default": ""
    },
    "DATABASE_URL": {
        "required_in_modes": ['cloud']
    }
}


# Core Settings
# -----------------------------------------------------------------------------
DEPLOYMENT_MODE = get_env_var("VISUALFOLIO_ENVIRONMENT", ENV_CONFIG["VISUALFOLIO_ENVIRONMENT"])
SECRET_KEY = get_env_var("DJANGO_SECRET_KEY", ENV_CONFIG["DJANGO_SECRET_KEY"], DEPLOYMENT_MODE)
DEBUG = get_env_var("DJANGO_DEBUG", ENV_CONFIG["DJANGO_DEBUG"], DEPLOYMENT_MODE)
ALLOWED_HOSTS = get_env_var("DJANGO_ALLOWED_HOSTS", ENV_CONFIG["DJANGO_ALLOWED_HOSTS"], DEPLOYMENT_MODE).split(",")

# CSRF Configuration
csrf_origins_str = get_env_var("DJANGO_CSRF_TRUSTED_ORIGINS", ENV_CONFIG["DJANGO_CSRF_TRUSTED_ORIGINS"], DEPLOYMENT_MODE)
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins_str.split(',') if origin.strip()] if csrf_origins_str else []


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


# Database and session config
# -----------------------------------------------------------------------------
if DEPLOYMENT_MODE == 'cloud':
    database_url = get_env_var("DATABASE_URL", ENV_CONFIG["DATABASE_URL"], DEPLOYMENT_MODE)
    DATABASES = {
        'default': dj_database_url.parse(database_url)
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    STATICFILES_DIRS = []

else:
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
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
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
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Base logging configuration for all environments
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Specific logging settings for different environments
if DEPLOYMENT_MODE == 'local':
    # Local deployment uses file logging
    if DEBUG:
        LOGGING['handlers']['console']['formatter'] = 'verbose'
        LOGGING['loggers']['']['level'] = 'DEBUG'
    
    # Add file handlers for local deployment
    LOGGING['handlers'].update({
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
        }
    })
    
    # Add file handlers to logger configurations
    LOGGING['loggers'].update({
        'visualfolio': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'visualfolio_scheduled_tasks': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file_error'],
            'level': 'ERROR',
            'propagate': False,
        },
    })
elif DEPLOYMENT_MODE == 'cloud':
    # Cloud deployment only logs to console
    pass
else:
    raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}. Must be 'local' or 'cloud'.")