from datetime import timedelta, datetime
from rest_framework import serializers
from django.db.models import F, Sum

from .models import (
    Courses,
    CourseLesson,
    CourseRatings,
    CourseChapter,
    EnrolledCourses,
)
from users.serializers import (
    RetrieveSellerSerializer,
)
from common.serializers import (
    RetrieveCourseCategorySerializer,
    RetrieveCourseSubCategorySerializer,
)
from utilities.permissions import (
    IsSellerPermission,
    IsSuperAdminPermission,
)
from utilities.aws import generate_pre_signed_url
from utilities.mixins import DynamicFieldsSerializerMixin


class ChangeCourseSerializer(serializers.ModelSerializer):
    """
    Serializer class for saving and updating courses.
    """
    is_available_for_published = serializers.SerializerMethodField(default=False)

    def get_is_available_for_published(self, obj):
        """
        Method to update is available for published
        """
        chapters_count = CourseChapter.objects.filter(course=obj.id).count()
        lesson_count = CourseLesson.objects.filter(chapter__course=obj.id).count()
        if obj.title and obj.short_description and obj.description and obj.what_student_learn and obj.requirements and obj.level and obj.audio_language and obj.category and obj.sub_category and obj.course_thumbnail_image and obj.course_thumbnail_video and obj.course_price and obj.sale_price and chapters_count > 0 and lesson_count > 0 and (
                obj.course_status == "DRAFT" or obj.course_status == "UN_PUBLISHED"):
            return True
        else:
            return False

    class Meta:
        model = Courses
        fields = ("id", "title", "seller", "category", "sub_category", "sale_price", "course_status",
                  "is_available_for_published",
                  "is_deleted", "created_by", "updated_by", "created_at", "updated_at")
        extra_kwargs = {
            "slug_name": {"required": False},
        }


class RetrieveCourseSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    """
    Serializer class for getting courses.
    """
    seller = serializers.CharField(read_only=True)
    seller_obj = serializers.SerializerMethodField(read_only=True)
    category_obj = serializers.SerializerMethodField(read_only=True)
    sub_category_obj = serializers.SerializerMethodField(read_only=True)
    chapters = serializers.SerializerMethodField(read_only=True)
    chapters_count = serializers.SerializerMethodField(read_only=True)
    ratings_obj = serializers.SerializerMethodField(read_only=True)
    course_duration = serializers.SerializerMethodField(read_only=True)
    lesson_count = serializers.SerializerMethodField(read_only=True)
    is_available_for_published = serializers.SerializerMethodField(read_only=True)

    def get_lesson_count(self, obj):
        """
        Method to get chapter count
        """
        lesson_count = CourseLesson.objects.filter(chapter__course=obj.id).count()
        return lesson_count

    def get_category_obj(self, obj):
        """
        Method to get category_obj
        """
        category_obj = obj.category
        if category_obj:
            return RetrieveCourseCategorySerializer(category_obj, many=False,
                                                    fields=self.context.get("category_obj", None)).data
        return None

    def get_sub_category_obj(self, obj):
        """
        Method to get sub_category_obj
        """
        sub_category_obj = obj.sub_category
        if sub_category_obj:
            return RetrieveCourseSubCategorySerializer(sub_category_obj, many=False,
                                                       fields=self.context.get("sub_category_obj", None)).data
        return None

    def get_chapters(self, obj):
        """
        Method to get chapters
        """
        chapters = CourseChapter.objects.filter(course=obj.id).order_by("order_no")
        if chapters:
            return RetrieveChapterSerializer(chapters, many=True, fields=self.context.get("chapters", None),
                                             context=self.context).data
        return None

    def get_chapters_count(self, obj):
        """
        Method to get chapter count
        """
        chapters_count = CourseChapter.objects.filter(course=obj.id).count()
        return chapters_count

    def get_seller_obj(self, obj):
        """
        Method to get seller
        """
        seller = obj.seller.seller_user.annotate(
            user_first_name=F("user__first_name"),
            user_last_name=F("user__last_name"),
            user_profile_image=F("user__profile_image"),
            user_profile_image_key=F("user__profile_image"),
        ).get()
        if seller:
            return RetrieveSellerSerializer(seller, many=False, fields=self.context.get("seller_obj", None)).data
        return None

    def get_ratings_obj(self, obj):
        """
        Method to get rating_obj
        """
        # list of reviews
        reviews = CourseRatings.objects.filter(course=obj.id).annotate(
            user_first_name=F("user__first_name"),
            user_last_name=F("user__last_name"),
            user_profile_image=F("user__profile_image"),
            user_profile_image_key=F("user__profile_image"),
        ).order_by("-created_at")

        # calculate total number of ratings and reviews.
        list_stars_rating = list(reviews.values_list("rating", flat=True))
        sum_of_rating_star = sum(list_stars_rating)
        length_of_rating_star = len(list_stars_rating)
        if length_of_rating_star > 0:
            total_rating = round(sum_of_rating_star / length_of_rating_star, 2)
        else:
            total_rating = 0

        # calculate all 5 star individual percentage.
        all_star_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        all_star_percentage = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        if length_of_rating_star != 0:
            for rating_star in list_stars_rating:
                all_star_count[rating_star] += 1
            for key, value in all_star_count.items():
                all_star_percentage[key] = int((value / length_of_rating_star) * 100)

        reviews_list = RetrieveRatingSerializer(reviews, many=True, fields=self.context.get("review_obj", None)).data
        return {
            "total_rating": total_rating,
            "total_reviews_count": length_of_rating_star,
            "all_star_percentage": all_star_percentage,
            "reviews_obj": reviews_list
        }

    def get_course_duration(self, obj):
        """
        Method to get course duration.
        """
        time_list = CourseLesson.objects.filter(chapter__course=obj.id).aggregate(total=Sum('duration'))
        if time_list["total"]:
            d = datetime(1, 1, 1) + time_list["total"]
            if d.day - 1 == 0:
                total_time_as_time = "{0}:{1}:{2}".format(d.hour, d.minute, d.second)
            else:
                hour = (d.day - 1) * 24 + d.hour
                total_time_as_time = "{0}:{1}:{2}".format(hour, d.minute, d.second)
        else:
            total_time_as_time = "00:00"
        return total_time_as_time

    def get_is_available_for_published(self, obj):
        """
        Method to get is course publishable
        """
        chapters_count = self.get_chapters_count(obj)
        lesson_count = self.get_lesson_count(obj)
        if obj.title and obj.short_description and obj.description and obj.what_student_learn and obj.requirements and obj.level and obj.audio_language and obj.category and obj.sub_category and obj.course_thumbnail_image and obj.course_thumbnail_video and obj.course_price and obj.sale_price and chapters_count > 0 and lesson_count > 0 and (
                obj.course_status == "DRAFT" or obj.course_status == "UN_PUBLISHED"):
            return True
        else:
            return False

    class Meta:
        model = Courses
        fields = ("id", "title", "seller", "short_description", "description", "what_student_learn", "requirements",
                  "level", "audio_language", "category", "sub_category", "course_thumbnail_image", "is_course_free",
                  "course_thumbnail_video", "course_price", "sale_price", "course_status", "is_deleted", "created_by",
                  "category_obj", "seller_obj", "audio_language_obj", "slug_name", "updated_by", "created_at",
                  "sub_category_obj", "updated_at", "course_thumbnail_image_key", "course_thumbnail_video_key",
                  "chapters", "chapters_count", "lesson_count", "ratings_obj", "enrolled_user_count", "course_duration",
                  "is_popular_badge", "is_new_badge", "is_available_for_published", "is_best_seller_badge",
                  "course_views")


class ChangeChapterSerializer(serializers.ModelSerializer):
    """
    Serializer class for saving and updating chapters.
    """

    class Meta:
        model = CourseChapter
        fields = ("id", "course", "title", "order_no", "is_deleted", "created_by",
                  "updated_by", "created_at", "updated_at")


class RetrieveChapterSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    """
    Serializer class for retrieve chapters.
    """
    lessons = serializers.SerializerMethodField(read_only=True)
    lesson_summary = serializers.SerializerMethodField(read_only=True)

    def get_lessons(self, obj):
        """
        Method to get lesson list.
        """
        lessons = obj.chappter_lesson.all().order_by("order_no")
        return RetrieveLessonSerializer(lessons, many=True, fields=self.context.get("lessons", None),
                                        context=self.context).data

    def get_lesson_summary(self, obj):
        """
        Method to get lesson summary.
        """
        time_list = obj.chappter_lesson.all().values_list("duration", flat=True)
        duration_in_sec = obj.chappter_lesson.all().aggregate(total=Sum('duration'))

        if duration_in_sec["total"]:
            d = datetime(1, 1, 1) + duration_in_sec["total"]
            if d.day - 1 == 0:
                total_time_as_time = "{0}:{1}:{2}".format(d.hour, d.minute, d.second)
            else:
                hours = ((d.day - 1) * 24) + d.hour
                total_time_as_time = "{0}:{1}:{2}".format(hours, d.minute, d.second)

        else:
            total_time_as_time = "00:00"
        return {
            "lessons_duration": total_time_as_time,
            "lesson_count": len(time_list)
        }

    class Meta:
        model = CourseChapter
        fields = ("id", "course", "title", "order_no", "is_deleted", "created_by", "lessons",
                  "updated_by", "created_at", "updated_at", "lesson_summary")


class ChangeLessonSerializer(serializers.ModelSerializer):
    """
    Serializer class for saving and updating lessons.
    """

    class Meta:
        model = CourseLesson
        fields = ("id", "chapter", "title", "video", "order_no", "duration", "is_deleted", "created_by",
                  "updated_by", "created_at", "updated_at")


class RetrieveLessonSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    """
    Serializer class for saving and updating lessons.
    """
    video_obj = serializers.SerializerMethodField(read_only=True)
    duration = serializers.SerializerMethodField(read_only=True)

    def get_duration(self, obj):
        d = obj.duration
        d = datetime(1, 1, 1) + d
        if d.day - 1 == 0:
            total_time_as_time = "{0}:{1}:{2}".format(d.hour, d.minute, d.second)
        else:
            hours = ((d.day - 1) * 24) + d.hour
            total_time_as_time = "{0}:{1}:{2}".format(hours, d.minute, d.second)
        return total_time_as_time

    def get_video_obj(self, obj):
        """
        Method to get video with proper permission.
        """
        request = self.context.get("request", None)
        if request and request.user.is_authenticated:
            is_allowed = False
            # check for super admin.
            super_admin_perm = IsSuperAdminPermission()
            if super_admin_perm.has_permission(request, self):
                is_allowed = True

            # check seller permission.
            seller_perm = IsSellerPermission()
            if not is_allowed and seller_perm.has_permission(request,
                                                             self) and obj.chapter.course.seller.id == request.user.id:
                is_allowed = True

            if not is_allowed and EnrolledCourses.objects.filter(course=obj.chapter.course.id,
                                                                 user=request.user.id).first():
                is_allowed = True

            if is_allowed:
                return {
                    "url": obj.video,
                    "key": generate_pre_signed_url(obj.video)
                }
        return {}

    class Meta:
        model = CourseLesson
        fields = ("id", "chapter", "title", "video_obj", "order_no", "duration", "is_deleted", "created_by",
                  "updated_by", "created_at", "updated_at")


class ChangeRatingSerializer(serializers.ModelSerializer):
    """
    Serializer class for saving and updating rating.
    """

    class Meta:
        model = CourseRatings
        fields = ("id", "course", "user", "rating", "title", "description", "is_deleted", "created_by",
                  "updated_by", "created_at", "updated_at")


class RetrieveRatingSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    """
    Serializer class for getting rating.
    """
    user_first_name = serializers.CharField(read_only=True)
    user_last_name = serializers.CharField(read_only=True)
    user_profile_image = serializers.SerializerMethodField(read_only=True)
    user_profile_image_key = serializers.CharField(read_only=True)

    def get_user_profile_image(self, obj):
        """
        Method to get profile_image.
        """
        return generate_pre_signed_url(obj.user_profile_image)

    class Meta:
        model = CourseRatings
        fields = ("id", "course", "user", "rating", "title", "description", "is_deleted", "created_by",
                  "updated_by", "created_at", "updated_at", "user_first_name", "user_last_name", "user_profile_image",
                  "user_profile_image_key")
