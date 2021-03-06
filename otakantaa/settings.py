# coding=utf-8

from __future__ import unicode_literals, absolute_import
from datetime import timedelta
from celery.schedules import crontab

"""
Django settings for otakantaa project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

APP_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
BASE_DIR = os.path.dirname(APP_DIR)

BASE_URL = 'http://127.0.0.1:8000'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3l5iwcwdk5o7+aonksliy75^oti^u7q2ktcg7y@8_jn1un)h(@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
PROJECT_APPS = (
    'otakantaa',
    'account',
    'organization',
    'libs.fimunicipality',
    'libs.djcontrib',
    'libs.permitter',
    'libs.attachtor',
    'libs.ajaxy',
    'libs.moderation',
    'omnavi',
    'content',
    'tagging',
    'otakantaa.apps.OtakantaaConversationAppConfig',
    'otakantaa.apps.OtakantaaSurveyAppConfig',
    'favorite',
    'okmessages',
    'okmoderation',
    'okadmin',
    'okwidget',
    'help',
    'actions',
    'openapi',
)

NON_PROJECT_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap3',
    'djangobower',
    'compressor',
    'imagekit',
    'celery',
    'social.apps.django_app.default',
    'libs.multilingo',
    'libs.bs3extras',
    'django_bleach',
    'redactor',
    'bootstrap3_datetime',
    'ordered_model',
    'libs.formidable',
    'nocaptcha_recaptcha',
    'wkhtmltopdf',
    'mptt',
    'twitter_tag',
    'rest_framework',
    'rest_framework_swagger',
)

TEST_APPS = (
    'libs.formidable.tests',
)

INSTALLED_APPS = PROJECT_APPS + NON_PROJECT_APPS

if len(sys.argv) > 1 and sys.argv[1] in ('test', 'jenkins'):
    INSTALLED_APPS += TEST_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'content.middleware.RequestParticipationMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social.backends.facebook.Facebook2OAuth2',
)

ROOT_URLCONF = 'otakantaa.urls'

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
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
                'otakantaa.context_processors.otakantaa_settings',
                'django.core.context_processors.i18n',
                'libs.permitter.context_processors.permitter',
            ],
            'debug': [
                'TEMPLATE_DEBUG',
            ],
        },
    },
]

AUTH_USER_MODEL = 'account.User'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(APP_DIR, 'static-tmp')

STATICFILES_DIRS = ()

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder',
    'compressor.finders.CompressorFinder',
)

BOWER_INSTALLED_APPS = (
    'select2#3.5.4',
    'select2-bootstrap3-css#1.4.6',
    'jquery-form#3.46.0',
    'underscore#1.8.3',
    'bootstrap3-datetimepicker#4.15.35',
    'bootstrap#3.3.5',
    'jquery.expander#1.6.0',
    'fontawesome#4.4.0',
    'jquery#2.1.4',
    'bootstrap-sass-official#3.1.1+2',
    'babylon-grid#2.2',
    'jquery-goup#1.0.0',
)

BOWER_COMPONENTS_ROOT = STATIC_ROOT

SASS_CACHE_PATH = os.path.join(STATIC_ROOT, 'sass')

COMPRESS_PRECOMPILERS = (
    (
        'text/x-scss',
        'sass --scss "{infile}" "{outfile}" '
        '-I "%s/bower_components" --cache-location="%s"' % (
            BOWER_COMPONENTS_ROOT,
            SASS_CACHE_PATH,
        )
    ),
)

COMPRESS_ENABLED = True

BOOTSTRAP3 = {
    'form_renderers': {
        'default': 'bootstrap3.renderers.FormRenderer',
        'preview': 'libs.bs3extras.renderers.FormPreviewRenderer',
        'notification_options_preview': 'bootstrap3.renderers.FormRenderer',
    },
    'field_renderers': {
        'default': 'otakantaa.forms.renderers.OtakantaaFieldRenderer',
        'inline': 'bootstrap3.renderers.InlineFieldRenderer',
        'preview': 'libs.bs3extras.renderers.WrapIdFieldPreviewRenderer',
        'notification_options_preview': 'account.renderers.'
                                        'NotificationOptionsFieldPreviewRenderer',
    },
    'required_css_class': 'required',
}

WSGI_APPLICATION = 'otakantaa.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'fi'

LANGUAGES = (
    ('fi', 'Suomeksi'),
    ('sv', 'På svenska'),
)

TIME_ZONE = 'Europe/Helsinki'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGIN_URL = '/kayttaja/kirjaudu-sisaan/'

LOGIN_REDIRECT_URL = '/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'local', 'media')

ENV_NAME = os.environ.get('DJANGO_SETTINGS_MODULE', 'dev').split('.')[-1]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "PARSER_CLASS": "redis.connection.HiredisParser",
        },
        "KEY_PREFIX": "otka:%s:cache" % ENV_NAME
    },
    "session": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "PARSER_CLASS": "redis.connection.HiredisParser",
        },
        "KEY_PREFIX": "otka:%s:session" % ENV_NAME
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


PRACTICE = False  # Is this a practice environment?

FORMAT_MODULE_PATH = 'otakantaa.formats'

REDACTOR_OPTIONS = {}

BLEACH_ALLOWED_TAGS = ['p', 'div', 'a', 'em', 'strong', 'del', 'img',
                       'ul', 'ol', 'li',
                       'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'pre',
                       'table', 'tbody', 'thead', 'tr', 'td', 'th',
                       'iframe']
BLEACH_STRIP_TAGS = True
BLEACH_ALLOWED_ATTRIBUTES = {
    '*': ['style', 'title', ],
    'a': ['href', 'rel', 'target', ],
    'img': ['src', 'alt', ],
    'iframe': ['src', 'frameborder', 'height', 'width', ],
    'td': ['colspan', 'rowspan', ],
}
BLEACH_ALLOWED_STYLES = ['font-family', 'font-weight', 'text-decoration', 'font-variant',
                         'text-align', 'width', 'height', 'margin', 'margin-left',
                         'margin-right', 'margin-top', 'margin-bottom', 'float', ]

CLAMAV = {
    'enabled': False,
}

TEST_RUNNER = 'otakantaa.test.runner.TestRunner'
DEFAULT_TEST_PATTERN = 'tests.py'

NOCAPTCHA = True
RECAPTCHA_USE_SLL = False

LOCALE_PATHS = (
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'otakantaa', 'locale'),
)

FILE_UPLOAD_ALLOWED_EXTENSIONS = [
    'jpg', 'jpeg', 'png', 'gif',
    'txt',
    'json',
    'xml',
    'csv',
    'mp3', 'ogg',
    'mp4', 'avi', 'mpg', 'mpeg', 'mkv',
    'pdf',
    'doc', 'docx',
    'odt', 'ods', 'odp',
    'xls', 'xlsx',
    'ppt', 'pps', 'pptx', 'ppsx',
]

ATTACHMENTS = {
    'max_size': 5 * 1024 * 1024,
    'max_attachments_per_object': 10,
    'max_size_per_uploader': 50 * 1024 * 1024,
    'max_size_per_uploader_timeframe': timedelta(hours=24),
}

BROKER_URL = 'redis://localhost:6379/11'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/11'
CELERY_IGNORE_RESULT = True
CELERY_DEFAULT_QUEUE = 'otka'
CELERY_ACCEPT_CONTENT = ['json', ]
CELERY_TASK_SERIALIZER = 'json'
CELERY_SEND_TASK_ERROR_EMAILS = True

CELERYBEAT_SCHEDULE = {
    'archive-idle-schemes': {
        'task': 'content.tasks.archive_idle_schemes',
        'schedule': crontab(hour=12, minute=15),
    },
    'warn-before-archive': {
        'task': 'content.tasks.warn_of_archiving',
        'schedule': crontab(hour=12, minute=30),
    },
    'daily-notifications': {
        'task': 'actions.tasks.create_daily_notifications',
        'schedule': crontab(hour=0, minute=0),
    },
    'weekly-notifications': {
        'task': 'actions.tasks.create_weekly_notifications',
        'schedule': crontab(day_of_week=6, hour=0, minute=0),
    },
}

FB_LOGO_URL = 'otakantaa/img/otakantaa_merkki_210x210.png'

SITE_NAME = 'otakantaa.fi'
SITE_NAME_PRACTICE = 'otakantaa.fi-harjoittelu'

SOCIAL_AUTH_FACEBOOK_SCOPE = ['public_profile', 'email']
SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'account.pipeline.performed_action',
    'account.pipeline.social_user',
    'account.pipeline.social_login_possible',
    'account.pipeline.prevent_duplicate_signup',
    'account.pipeline.social_signup',
    'account.pipeline.logged_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
    'account.pipeline.set_messages'
)
SOCIAL_AUTH_DISCONNECT_PIPELINE = (
    'social.pipeline.disconnect.allowed_to_disconnect',
    'social.pipeline.disconnect.get_entries',
    'social.pipeline.disconnect.revoke_tokens',
    'social.pipeline.disconnect.disconnect',
    'account.pipeline.set_disconnect_messages'
)
FIELDS_STORED_IN_SESSION = ["action"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'name, email'
}

AUTO_ARCHIVE_DAYS = 120
AUTO_ARCHIVE_WARNING_DAYS = 30

HOT_DAYS = 14
HOTNESS_POINTS = 1000000

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'openapi.permissions.ReadOnly',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
        'openapi.renderers.XMLRenderer',
    ],
}

OPEN_API = {
    'version': '0.1'
}

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': OPEN_API['version'],
    'doc_expansion': 'list',
    'template_path': 'openapi/docs/index.html',
    'info': {
        'title': 'Open Data API v0.1',
        'description': ''
        # HACK: long html description gets injected by
        # opendata.decorators.swagger_api_description_hack
    },
}
