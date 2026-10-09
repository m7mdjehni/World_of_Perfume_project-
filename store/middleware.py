from .models import PageVisit

# Paths we never want to count as a "visit" — admin, static assets, and the
# JSON API (those are data/requests, not someone browsing the site).
_EXCLUDED_PREFIXES = ("/admin", "/static", "/media", "/api")


class VisitorTrackingMiddleware:
    """Logs one PageVisit row per real GET page view on the storefront.

    Kept deliberately simple: no cookies/sessions involved, so it counts
    hits rather than unique visitors.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.method == "GET"
            and response.status_code == 200
            and not request.path.startswith(_EXCLUDED_PREFIXES)
        ):
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")
            try:
                PageVisit.objects.create(path=request.path, ip_address=ip_address or None)
            except Exception:
                # Never let visitor logging break the actual page response.
                pass

        return response
