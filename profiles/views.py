from django.core.paginator import Paginator, EmptyPage
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Profile, PlatformUser
from .serializers import ProfileSerializer, ProfileQuerySerializer
from .services import parse_natural_language_query
from .auth_tokens import create_access_token, create_refresh_token, rotate_refresh_token
from .authentication import JWTAuthentication
from .permissions import IsAdmin, IsAnalystOrAdmin
from .web_auth import CookieJWTAuthentication

import urllib.parse
import requests
import csv


def apply_profile_filters(queryset, params):
    gender = params.get("gender")
    age_group = params.get("age_group")
    country_id = params.get("country_id")
    min_age = params.get("min_age")
    max_age = params.get("max_age")
    min_gender_probability = params.get("min_gender_probability")
    min_country_probability = params.get("min_country_probability")
    sort_by = params.get("sort_by", "created_at")
    order = params.get("order", "desc")

    allowed_sort_fields = [
        "name",
        "gender",
        "age",
        "age_group",
        "country_id",
        "gender_probability",
        "country_probability",
        "created_at",
    ]

    if sort_by not in allowed_sort_fields:
        sort_by = "created_at"

    if order not in ["asc", "desc"]:
        order = "desc"

    if gender:
        queryset = queryset.filter(gender=gender)

    if age_group:
        queryset = queryset.filter(age_group=age_group)

    if country_id:
        queryset = queryset.filter(country_id=country_id)

    if min_age is not None:
        queryset = queryset.filter(age__gte=min_age)

    if max_age is not None:
        queryset = queryset.filter(age__lte=max_age)

    if min_gender_probability is not None:
        queryset = queryset.filter(gender_probability__gte=min_gender_probability)

    if min_country_probability is not None:
        queryset = queryset.filter(country_probability__gte=min_country_probability)

    ordering = sort_by if order == "asc" else f"-{sort_by}"
    return queryset.order_by(ordering)


def paginate_profiles(queryset, page, limit):
    paginator = Paginator(queryset, limit)

    try:
        page_obj = paginator.page(page)
        results = page_obj.object_list
    except EmptyPage:
        results = []

    data = ProfileSerializer(results, many=True).data

    return {
        "pagination": {
            "page": page,
            "limit": limit,
            "total": paginator.count,
            "pages": paginator.num_pages,
        },
        "data": data,
    }


class ProfileCollectionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAnalystOrAdmin]

    def get_age_group(self, age):
        if age <= 12:
            return "child"
        if age <= 19:
            return "teenager"
        if age <= 59:
            return "adult"
        return "senior"

    def build_profile_data(self, name):
        gender_response = requests.get(
            "https://api.genderize.io",
            params={"name": name},
            timeout=10,
        )

        age_response = requests.get(
            "https://api.agify.io",
            params={"name": name},
            timeout=10,
        )

        country_response = requests.get(
            "https://api.nationalize.io",
            params={"name": name},
            timeout=10,
        )

        if (
            gender_response.status_code != 200
            or age_response.status_code != 200
            or country_response.status_code != 200
        ):
            raise Exception("External API request failed")

        gender_data = gender_response.json()
        age_data = age_response.json()
        country_data = country_response.json()

        countries = country_data.get("country", [])
        top_country = countries[0] if countries else {}

        age = age_data.get("age") or 0
        country_id = top_country.get("country_id") or "unknown"

        return {
            "name": name,
            "gender": gender_data.get("gender") or "unknown",
            "gender_probability": gender_data.get("probability") or 0,
            "age": age,
            "age_group": self.get_age_group(age),
            "country_id": country_id,
            "country_name": country_id,
            "country_probability": top_country.get("probability") or 0,
        }

    def get(self, request):
        serializer = ProfileQuerySerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                {"status": "error", "message": "Invalid query parameters"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        params = serializer.validated_data
        page = params.get("page", 1)
        limit = params.get("limit", 10)

        queryset = Profile.objects.all()
        queryset = apply_profile_filters(queryset, params)

        paginated_result = paginate_profiles(queryset, page, limit)

        return Response(
            {
                "status": "success",
                **paginated_result,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        name = request.data.get("name")

        if not isinstance(name, str):
            return Response(
                {"status": "error", "message": "Invalid type"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        name = name.strip().lower()

        if not name:
            return Response(
                {"status": "error", "message": "Missing or empty name"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_profile = Profile.objects.filter(name=name).first()

        if existing_profile:
            return Response(
                {
                    "status": "success",
                    "message": "Profile already exists",
                    "data": ProfileSerializer(existing_profile).data,
                },
                status=status.HTTP_200_OK,
            )

        try:
            profile_data = self.build_profile_data(name)

            allowed_fields = {field.name for field in Profile._meta.fields}

            clean_data = {
                key: value
                for key, value in profile_data.items()
                if key in allowed_fields
            }

            profile = Profile.objects.create(**clean_data)

            return Response(
                {
                    "status": "success",
                    "message": "Profile created successfully",
                    "data": ProfileSerializer(profile).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception:
            return Response(
                {
                    "status": "error",
                    "message": "Failed to create profile",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )


class ProfileSearchView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        query = request.query_params.get("q") or request.query_params.get("query", "")
        query = query.strip()

        if not query:
            return Response(
                {"status": "error", "message": "Missing or empty parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parsed_filters = parse_natural_language_query(query)

        extra_params = {
            "page": request.query_params.get("page", 1),
            "limit": request.query_params.get("limit", 10),
            "sort_by": request.query_params.get("sort_by", "created_at"),
            "order": request.query_params.get("order", "desc"),
        }

        queryset = Profile.objects.all()

        if parsed_filters:
            merged_params = {**parsed_filters, **extra_params}
            serializer = ProfileQuerySerializer(data=merged_params)

            if not serializer.is_valid():
                return Response(
                    {"status": "error", "message": "Invalid query parameters"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            params = serializer.validated_data
            queryset = apply_profile_filters(queryset, params)

        else:
            serializer = ProfileQuerySerializer(data=extra_params)

            if not serializer.is_valid():
                return Response(
                    {"status": "error", "message": "Invalid query parameters"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            params = serializer.validated_data
            queryset = queryset.filter(name__icontains=query)
            queryset = apply_profile_filters(queryset, params)

        page = params.get("page", 1)
        limit = params.get("limit", 10)

        paginated_result = paginate_profiles(queryset, page, limit)

        return Response(
            {
                "status": "success",
                "query": query,
                **paginated_result,
            },
            status=status.HTTP_200_OK,
        )


class ProfileExportView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get(self, request):
        serializer = ProfileQuerySerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                {"status": "error", "message": "Invalid query parameters"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        params = serializer.validated_data
        queryset = Profile.objects.all()
        queryset = apply_profile_filters(queryset, params)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="profiles.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "id",
            "name",
            "gender",
            "gender_probability",
            "age",
            "age_group",
            "country_id",
            "country_name",
            "country_probability",
            "created_at",
        ])

        for profile in queryset:
            writer.writerow([
                profile.id,
                profile.name,
                profile.gender,
                profile.gender_probability,
                profile.age,
                profile.age_group,
                profile.country_id,
                getattr(profile, "country_name", ""),
                profile.country_probability,
                profile.created_at,
            ])

        return response


def github_login(request):
    base_url = "https://github.com/login/oauth/authorize"

    redirect_uri = getattr(
        settings,
        "GITHUB_REDIRECT_URI",
        "http://127.0.0.1:8000/api/v1/auth/github/callback/",
    )

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)


def github_callback(request):
    code = request.GET.get("code")

    if not code:
        return JsonResponse(
            {"status": "error", "message": "No code provided"},
            status=400,
        )

    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )

    token_data = token_response.json()
    github_access_token = token_data.get("access_token")

    if not github_access_token:
        return JsonResponse(
            {"status": "error", "message": "Failed to get access token"},
            status=400,
        )

    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {github_access_token}"},
        timeout=10,
    )

    user_data = user_response.json()

    github_id = user_data.get("id")
    username = user_data.get("login")

    if not github_id or not username:
        return JsonResponse(
            {"status": "error", "message": "Invalid GitHub user data"},
            status=400,
        )

    user, created = PlatformUser.objects.get_or_create(
        github_id=github_id,
        defaults={
            "username": username,
            "role": "analyst",
        },
    )

    if not created:
        user.username = username
        user.save()

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return JsonResponse(
        {
            "status": "success",
            "message": "Authentication successful",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 900,
                "user": {
                    "id": str(user.id),
                    "github_id": user.github_id,
                    "username": user.username,
                    "role": user.role,
                },
            },
        }
    )


class TokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"status": "error", "message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = rotate_refresh_token(refresh_token)

        if not result:
            return Response(
                {"status": "error", "message": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = result["user"]

        return Response(
            {
                "status": "success",
                "message": "Token refreshed successfully",
                "data": {
                    "access_token": result["access_token"],
                    "refresh_token": result["refresh_token"],
                    "token_type": "Bearer",
                    "expires_in": 900,
                    "user": {
                        "id": str(user.id),
                        "github_id": user.github_id,
                        "username": user.username,
                        "role": user.role,
                    },
                },
            },
            status=status.HTTP_200_OK,
        )


class WebMeView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        user = request.user

        return Response(
            {
                "status": "success",
                "data": {
                    "id": str(user.id),
                    "github_id": user.github_id,
                    "username": user.username,
                    "role": user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class WebLogoutView(APIView):
    def post(self, request):
        response = Response(
            {
                "status": "success",
                "message": "Logged out successfully",
            },
            status=status.HTTP_200_OK,
        )

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response


def web_github_login(request):
    base_url = "https://github.com/login/oauth/authorize"

    redirect_uri = getattr(
        settings,
        "WEB_GITHUB_REDIRECT_URI",
        "http://127.0.0.1:8000/api/v1/web/auth/github/callback/",
    )

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)


def web_github_callback(request):
    code = request.GET.get("code")

    if not code:
        return JsonResponse(
            {"status": "error", "message": "No code provided"},
            status=400,
        )

    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )

    token_data = token_response.json()
    github_access_token = token_data.get("access_token")

    if not github_access_token:
        return JsonResponse(
            {"status": "error", "message": "Failed to get GitHub access token"},
            status=400,
        )

    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {github_access_token}"},
        timeout=10,
    )

    user_data = user_response.json()

    github_id = user_data.get("id")
    username = user_data.get("login")

    if not github_id or not username:
        return JsonResponse(
            {"status": "error", "message": "Invalid GitHub user data"},
            status=400,
        )

    user, created = PlatformUser.objects.get_or_create(
        github_id=github_id,
        defaults={
            "username": username,
            "role": "analyst",
        },
    )

    if not created:
        user.username = username
        user.save()

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    response = redirect("https://insighta-web-omega.vercel.app")

    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=900,
    )

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=60 * 60 * 24 * 7,
    )

    return response