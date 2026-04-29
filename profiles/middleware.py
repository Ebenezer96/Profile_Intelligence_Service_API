import logging
import time

logger = logging.getLogger("api_requests")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        user = getattr(request, "user", None)

        user_id = "anonymous"
        if user and getattr(user, "is_authenticated", False):
            user_id = getattr(user, "id", "authenticated")

        ip_address = self.get_client_ip(request)

        logger.info(
            "method=%s path=%s status=%s user=%s ip=%s duration_ms=%s",
            request.method,
            request.path,
            response.status_code,
            user_id,
            ip_address,
            duration_ms,
        )

        return response

    def get_client_ip(self, request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR", "")