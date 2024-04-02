from django.urls import path

from .views import (
    GetCourseCategoryListAPIView,
    GetCourseSubCategoryListAPIView,
)


urlpatterns = [
    path("getCourseCategoryList", GetCourseCategoryListAPIView.as_view(), name="get-course-category-list"),
    path("getCourseSubCategoryList", GetCourseSubCategoryListAPIView.as_view(), name="get-course-sub-category-list"),
]
