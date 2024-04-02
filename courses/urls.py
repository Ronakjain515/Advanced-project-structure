from django.urls import path

from .views import (
    LessonListAPIView,
    ListCourseAPIView,
    ChapterListAPIView,
    CourseFilterListAPIView,
)

urlpatterns = [
    path("listCourse", ListCourseAPIView.as_view(), name="list-course"),
    path("courseFliterList", CourseFilterListAPIView.as_view(), name="list-seller-course"),

    path("chapterList", ChapterListAPIView.as_view(), name="chapterL-lst"),

    path("lessonList", LessonListAPIView.as_view(), name="lesson-list"),

]
