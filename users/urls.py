from django.urls import path

from .views import (
    LoginAPIView,
    GetSellerListAPIView,
    GetSellerDetailsAPIView,
)


urlpatterns = [
    path("login", LoginAPIView.as_view(), name="login"),

    path("getSellerList", GetSellerListAPIView.as_view(), name="get-seller-list"),
    path("getSellerDetails/<slug:slug>/", GetSellerDetailsAPIView.as_view(), name="get-seller-details"),
]
