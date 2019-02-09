from django.contrib.sitemaps import Sitemap
from django_blog.django_blog.models import Post, Page


class PostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Post.objects.filter(status='Published')

    def lastmod(self, obj):
        return obj.published_on


class PageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Page.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.date_created