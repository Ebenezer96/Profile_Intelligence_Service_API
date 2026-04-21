from django.core.paginator import Paginator, EmptyPage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Profile
from .serializers import ProfileSerializer, ProfileQuerySerializer
from .services import parse_natural_language_query


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
    except EmptyPage:
        page_obj = []

    data = ProfileSerializer(page_obj, many=True).data

    return {
        "page": page,
        "limit": limit,
        "total": paginator.count,
        "data": data,
    }


class ProfileCollectionView(APIView):
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


class ProfileSearchView(APIView):
    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response(
                {"status": "error", "message": "Missing or empty parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parsed_filters = parse_natural_language_query(query)

        if not parsed_filters:
            return Response(
                {"status": "error", "message": "Unable to interpret query"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extra_params = {
            "page": request.query_params.get("page", 1),
            "limit": request.query_params.get("limit", 10),
            "sort_by": request.query_params.get("sort_by", "created_at"),
            "order": request.query_params.get("order", "desc"),
        }

        merged_params = {**parsed_filters, **extra_params}

        serializer = ProfileQuerySerializer(data=merged_params)

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