from .authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get("access_token")

        if not access_token:
            return None

        request.META["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
        return super().authenticate(request)