from django.conf import settings
import os

AWS_ENABLED = getattr(settings, 'AWS_ENABLED', False)
BASE_DIR = getattr(settings, 'BASE_DIR')
MEDIA_URL = settings.MEDIA_URL if settings.MEDIA_URL else '/media/'
MEDIA_ROOT = settings.MEDIA_ROOT if settings.MEDIA_ROOT else os.path.join(BASE_DIR + '/media/')
STATIC_ROOT = settings.STATIC_ROOT if settings.STATIC_ROOT else os.path.join(BASE_DIR, 'static')
STATIC_URL = settings.STATIC_URL if settings.STATIC_URL else '/static/'

DISQUS_SHORTNAME = getattr(settings, 'DISQUS_SHORTNAME', '')

BLOG_TITLE = "AITech Central"
BLOG_DESCRIPTION = "Self learning guide for AI"
BLOG_KEYWORDS = "Artificial Intelligence, Machine Learning, AI, ML"
BLOG_AUTHOR = "Sreenivasa Rao"
