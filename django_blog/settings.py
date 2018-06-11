from django.conf import settings
import os

AWS_ENABLED = getattr(settings, 'AWS_ENABLED', False)
BASE_DIR = getattr(settings, 'BASE_DIR')
MEDIA_URL = settings.MEDIA_URL if settings.MEDIA_URL else '/media/'  # settings.MEDIA_URL if settings.MEDIA_URL else '/media/'
MEDIA_ROOT = settings.MEDIA_ROOT if settings.MEDIA_ROOT else os.path.join(BASE_DIR + '/media/')  # settings.MEDIA_ROOT if settings.MEDIA_ROOT else os.path.join(BASE_DIR + '/media/')

DISQUS_SHORTNAME = getattr(settings, 'DISQUS_SHORTNAME', '')

BLOG_TITLE = "AI-Tech Central"
BLOG_DESCRIPTION = "Self learning guide for AI"
BLOG_KEYWORDS = "Artificial Intelligence, Machine Learning, AI, ML"
BLOG_AUTHOR = "Sreenivasa Rao"
