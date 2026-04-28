from django.urls import path
from .views import (
    ProfileCollectionView,
    ProfileSearchView,
    ProfileExportView,
    github_login,
    github_callback,
    TokenRefreshView,

    # NEW imports
    WebMeView,
    WebLogoutView,
    web_github_login,
    web_github_callback,
)

urlpatterns = [
    # ===== EXISTING API =====
    path("profiles/", ProfileCollectionView.as_view(), name="profile-collection"),
    path("profiles/search/", ProfileSearchView.as_view(), name="profile-search"),
    path("profiles/export/", ProfileExportView.as_view(), name="profile-export"),

    path("auth/github/login/", github_login, name="github-login"),
    path("auth/github/callback/", github_callback, name="github-callback"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # ===== NEW WEB AUTH (COOKIES) =====
    path("web/auth/github/login/", web_github_login, name="web-github-login"),
    path("web/auth/github/callback/", web_github_callback, name="web-github-callback"),
    path("web/auth/me/", WebMeView.as_view(), name="web-me"),
    path("web/auth/logout/", WebLogoutView.as_view(), name="web-logout"),
]