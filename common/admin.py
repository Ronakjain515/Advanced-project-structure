from django.contrib import admin

from .models import (
    CourseCategory,
    SubCourseCategory,
)

# Register your models here.
admin.site.register(CourseCategory)
admin.site.register(SubCourseCategory)