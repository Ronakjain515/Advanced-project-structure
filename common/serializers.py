from django.db.models import F
from rest_framework import serializers

from courses.models import Courses
from .models import (
    CourseCategory,
    SubCourseCategory,
)
from utilities.mixins import (
    DynamicFieldsSerializerMixin,
)


class ChangeCourseCategorySerializer(serializers.ModelSerializer):
    """
    Serializer class for adding and updating course category.
    """
    class Meta:
        model = CourseCategory
        fields = ("id", "name", "is_deleted", "created_by", "updated_by", "created_at", "updated_at")


class RetrieveCourseCategorySerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    """
    Serializer class for getting course category.
    """
    sub_category = serializers.SerializerMethodField(read_only=True)
    available_course_count = serializers.SerializerMethodField(read_only=True)
    value = serializers.CharField(read_only=True)

    def get_available_course_count(self, obj):
        """
        Method to get available courses count.
        """
        course_count = Courses.objects.filter(course_status="PUBLISHED", category=obj.id).count()
        return course_count

    def get_sub_category(self, obj):
        """
        Method to get sub-category list.
        """
        sub_category = obj.course_sub_category.all().annotate(
            category_name=F("category__name"),
            value=F("id")
        )
        return RetrieveCourseSubCategorySerializer(sub_category, many=True, fields=self.context.get("sub_category", None)).data

    class Meta:
        model = CourseCategory
        fields = ("id", "name", "value", "sub_category", "is_deleted", "created_by", "updated_by", "created_at", "updated_at", "available_course_count")


class ChangeCourseSubCategorySerializer(serializers.ModelSerializer):
    """
    Serializer class for adding and updating course sub-category.
    """
    class Meta:
        model = SubCourseCategory
        fields = ("id", "name", "category", "is_deleted", "created_by", "updated_by", "created_at", "updated_at")


class RetrieveCourseSubCategorySerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    """
    Serializer class for getting course sub-category.
    """
    category_name = serializers.CharField(read_only=True)
    category_id = serializers.IntegerField(read_only=True)
    value = serializers.CharField(read_only=True)

    class Meta:
        model = SubCourseCategory
        fields = ("id", "name", "value", "category", "category_name", "is_deleted", "created_by", "updated_by",
                  "category_id", "created_at", "updated_at")
