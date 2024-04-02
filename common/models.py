from django.db import models

from utilities.mixins import CustomModelMixin


class CourseCategory(CustomModelMixin):
    """
    Class for creating model for course category.
    """
    name = models.CharField(max_length=200, null=False, blank=False)


class SubCourseCategory(CustomModelMixin):
    """
    Class for creating model for course sub-category.
    """
    name = models.CharField(max_length=200, null=False, blank=False)
    category = models.ForeignKey(CourseCategory, null=False, blank=False, on_delete=models.CASCADE, related_name="course_sub_category")


