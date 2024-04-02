from django.contrib import admin

from .models import (
    Courses,
    CourseLesson,
    CourseRatings,
    CourseChapter,
    EnrolledCourses,
)

# Register your models here.
admin.site.register(Courses)
admin.site.register(CourseLesson)
admin.site.register(CourseRatings)
admin.site.register(CourseChapter)
admin.site.register(EnrolledCourses)
