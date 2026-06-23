from django.conf import settings

class DomainUrlConfMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]
        urlconf = getattr(settings, "URLCONFS_BY_HOST", {}).get(host)
        if urlconf:
            request.urlconf = urlconf
        return self.get_response(request)
