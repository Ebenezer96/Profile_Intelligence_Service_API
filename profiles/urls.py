from django.urls import path
from .views import ProfileCollectionView, ProfileSearchView

urlpatterns = [
    path("profiles/", ProfileCollectionView.as_view(), name="profile-collection"),
    path("profiles/search/", ProfileSearchView.as_view(), name="profile-search"),
]