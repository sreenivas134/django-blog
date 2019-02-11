from django_blog.django_blog.models import HitCount, UrlHit
from django.db import transaction


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def hit_count(request):
    if not request.session.session_key:
        request.session.save()
    # if request.path.startswith('/static') or request.path.startswith('/media') or request.path.startswith('/dashboard'):
    #     return 0
    s_key = request.session.session_key
    ip = get_client_ip(request)
    url, url_created = UrlHit.objects.get_or_create(url=request.path)
    user_agent = request.META['HTTP_USER_AGENT']
    if url_created:
        track, created = HitCount.objects.get_or_create(url_hit=url, ip=ip, session=s_key, user_agent=user_agent)
        transaction.commit()
        if created:
            url.increase()
            request.session[ip] = ip
            request.session[request.path] = request.path
    else:
        if ip and request.path not in request.session:
            track, created = HitCount.objects.get_or_create(url_hit=url, ip=ip, session=s_key, user_agent=user_agent)
            transaction.commit()
            if created:
                url.increase()
                request.session[ip] = ip
                request.session[request.path] = request.path
    return url.hits


class HitCountMiddleWare(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            hit_count(request)
        except:
            pass
        return self.get_response(request)
