import random

from django.db import models
from django.utils.text import slugify
from common.models import (
    CourseCategory,
    SubCourseCategory,
)
from utilities.constants import (
    CourseStatusChoices,
)
from users.models import CustomUser
from utilities.mixins import CustomModelMixin


class Courses(CustomModelMixin):
    """
    Class for creating model for courses.
    """
    slug_name = models.SlugField(max_length=500, null=False, blank=False, unique=True)
    seller = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE, related_name="course_seller")
    title = models.CharField(max_length=1000, null=False, blank=False)
    category = models.ForeignKey(CourseCategory, null=True, blank=False, on_delete=models.CASCADE, related_name="course_category")
    sub_category = models.ForeignKey(SubCourseCategory, null=True, blank=False, on_delete=models.CASCADE)
    course_status = models.CharField(max_length=50, null=False, blank=False, choices=CourseStatusChoices)
    sale_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=False)

    def save(self, *args, **kwargs):

        if self.pk:
            number = self.slug_name.split('-')[::-1]
            self.slug_name = slugify(self.title, "") + "-" + number[0]
        else:
            self.slug_name = slugify(self.title, "") + "-" + str(random.randint(1, 999))
        super().save(*args, **kwargs)


class CourseChapter(CustomModelMixin):
    """
    Class for creating model for course Chapters.
    """
    title = models.CharField(max_length=500, null=False, blank=False)
    course = models.ForeignKey(Courses, null=False, blank=False, on_delete=models.CASCADE, related_name="course_chapter")
    order_no = models.IntegerField(null=False, blank=False)


class CourseLesson(CustomModelMixin):
    """
    Class for creating model for course lesson.
    """
    chapter = models.ForeignKey(CourseChapter, null=False, blank=False, on_delete=models.CASCADE, related_name="chappter_lesson")
    title = models.CharField(max_length=500, null=False, blank=False)
    video = models.CharField(max_length=2000, null=False, blank=False)
    order_no = models.IntegerField(null=False, blank=False)
    duration = models.DurationField(null=False, blank=False)


class CourseRatings(CustomModelMixin):
    """
    Class for creating model for course rating.
    """
    course = models.ForeignKey(Courses, null=False, blank=False, on_delete=models.CASCADE, related_name="course_rating")
    user = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    rating = models.IntegerField(null=False, blank=False)
    title = models.CharField(max_length=500, null=False, blank=False)
    description = models.TextField(null=True, blank=False)


class EnrolledCourses(CustomModelMixin):
    """
    Class for creating model for enrolled courses.
    """
    course = models.ForeignKey(Courses, null=False, blank=False, on_delete=models.CASCADE, related_name="enrolled_courses")
    user = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE, related_name="enrolled_course_users")
