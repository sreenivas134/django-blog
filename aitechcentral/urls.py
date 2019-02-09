from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf import settings
from django.views.generic import TemplateView
from settings import MEDIA_ROOT
import django

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include('django_blog.urls')),
    url(r'^static/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.STATIC_ROOT}),
    url(r'^media/(?P<path>.*)$', django.views.static.serve, {'document_root': MEDIA_ROOT}),
    url(r'^robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots_file"),
]

urlpatterns = format_suffix_patterns(urlpatterns)