from datetime import timedelta

from django.db.models import OuterRef, Sum, FloatField, Avg, Subquery, F, Count, Q, IntegerField, Value, CharField
from django.db.models.functions import Coalesce, Concat
from django_filters import filters, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, filters
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from common.models import CourseCategory, SubCourseCategory
from courses.filters import CourseFilter
from courses.models import CourseChapter, Courses, CourseLesson
from courses.serializers import RetrieveCourseSerializer, RetrieveChapterSerializer, RetrieveLessonSerializer
from users.models import SellerProfile
from utilities import messages
from utilities.mixins import DynamicFieldsViewMixin
from utilities.permissions import IsTokenValid, IsActiveUserPermission
from utilities.utils import CustomPagination, ResponseInfo


class ListCourseAPIView(DynamicFieldsViewMixin, ListAPIView):
    """
    Class for creating api for listing courses.
    """
    permission_classes = [(IsAuthenticated & IsTokenValid & IsActiveUserPermission) | AllowAny]
    authentication_classes = (JWTAuthentication,)
    serializer_class = RetrieveCourseSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ("course_status",)
    search_fields = ['title']
    filterset_class = CourseFilter
    ordering_fields = ['sale_price', 'duration', "rating"]

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(ListCourseAPIView, self).__init__(**kwargs)

    def paginate_queryset(self, queryset):
        """
        Method for get paginated query set.
        """
        pagination = self.request.GET.get("pagination", "False")
        if pagination == "True" or pagination == "true":
            return super().paginate_queryset(queryset)
        return None

    def get_queryset(self):
        """
        Method to get queryset for course.
        """
        subquery = CourseChapter.objects.filter(
            course__id=OuterRef('id')
        ).values('course__id').annotate(
            total_duration=Sum('chappter_lesson__duration')
        ).values('total_duration')[:1]

        return Courses.objects.filter(course_status="PUBLISHED").annotate(
            rating=Coalesce(Avg("course_rating__rating"), 0, output_field=FloatField()),
            duration=Subquery(subquery),
        ).order_by("created_at")

    def get(self, request, *args, **kwargs):
        """
        GET Method for getting course list.
        """
        course_serializer = super().list(request, *args, **kwargs)

        self.response_format["data"] = course_serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
        self.response_format["message"] = [messages.SUCCESS]
        return Response(self.response_format, status=self.status_code)


class CourseFilterListAPIView(DynamicFieldsViewMixin, ListAPIView):
    """
    Class for creating api for listing courses.
    """
    permission_classes = [(IsAuthenticated & IsTokenValid & IsActiveUserPermission) | AllowAny]
    authentication_classes = (JWTAuthentication,)
    serializer_class = RetrieveCourseSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ("course_status",)
    search_fields = ['title']
    filterset_class = CourseFilter
    ordering_fields = ['sale_price', 'duration', "rating"]

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(CourseFilterListAPIView, self).__init__(**kwargs)

    def paginate_queryset(self, queryset):
        """
        Method for get paginated query set.
        """
        pagination = self.request.GET.get("pagination", "False")
        if pagination == "True" or pagination == "true":
            return super().paginate_queryset(queryset)
        return None

    def get_category(self, course_id):
        """
        Method to get category list
        """
        category_list = CourseCategory.objects.all().annotate(
            label=F('name'),
            value=F('id'),
            count=Count("course_category__id", filter=Q(course_category__id__in=course_id)),
        ).order_by("label").values("label", "value", "count")

        for category in category_list:
            subcategory_data = SubCourseCategory.objects.filter(category_id=category['value']).annotate(
                label=F('name'),
                value=F('id'),
                count=Count("courses__id", filter=Q(courses__id__in=course_id)),
            ).values('label', 'value', 'count')
            category['subcategory'] = list(subcategory_data)

        count = 0
        category = list(category_list)
        for category_obj in category:
            count += category_obj["count"]

        category.insert(0, {
            "label": 'All',
            "value": 0,
            "count": count
        })
        return category

    def get_rating(self, course_id):
        """
        Method to get rating list
        """
        queryset = Courses.objects.filter(id__in=course_id).annotate(
            rating=Coalesce(Avg("course_rating__rating"), 0, output_field=IntegerField())
        ).values("rating")

        rating_three = queryset.filter(course_rating__rating__gte=3)
        rating_three_five = queryset.filter(course_rating__rating__gte=3.5)
        rating_four = queryset.filter(course_rating__rating__gte=4)
        rating_four_five = queryset.filter(course_rating__rating__gte=4.5)

        data = [
            {
                "label": 'All',
                "value": 0,
                "count": queryset.count()
            },
            {
                "label": '4.5',
                "value": 4.5,
                "count": rating_four_five.count(),
            },
            {
                "label": '4',
                "value": 4,
                "count": rating_four.count(),
            },
            {
                "label": '3.5',
                "value": 3.5,
                "count": rating_three_five.count(),
            },
            {
                "label": '3',
                "value": 3,
                "count": rating_three.count()
            }
        ]
        return data

    def get_seller(self, course_id):
        """
        Method to get seller list with course count
        """
        seller = SellerProfile.objects.all().annotate(
            value=F('user__id'),
            label=Concat(F('user__first_name'), Value(" "), F('user__last_name'), output_field=CharField()),
            count=Count('user__course_seller__id', filter=Q(user__course_seller__id__in=course_id))
        ).order_by("label").values("label", "value", "count")

        count = 0
        seller = list(seller)
        for seller_obj in seller:
            count += seller_obj["count"]

        seller.insert(0, {
            "label": "All",
            "value": 0,
            "count": count
        })
        return seller

    def get_duration(self, course_id):
        """
        Method to get duration with course count
        """
        duration_4_to_compare = timedelta(hours=4, minutes=0, seconds=0)
        duration_7_to_compare = timedelta(hours=7, minutes=0, seconds=0)
        duration_20_to_compare = timedelta(hours=20, minutes=0, seconds=0)

        subquery = CourseChapter.objects.filter(
            course__id=OuterRef('id')
        ).values('course__id').annotate(
            total_duration=Sum('chappter_lesson__duration')
        ).values('total_duration')[:1]

        queryset = Courses.objects.filter(id__in=course_id).annotate(
            duration=Subquery(subquery),
        )

        duration_4_less = queryset.filter(duration__lt=duration_4_to_compare)

        duration_4_7_bet = queryset.filter(duration__gte=duration_4_to_compare, duration__lt=duration_7_to_compare)

        duration_7_20_bet = queryset.filter(duration__gte=duration_7_to_compare, duration__lt=duration_20_to_compare)

        duration_20_plus = queryset.filter(duration__gte=duration_20_to_compare)

        data = [
            {
                "label": "All",
                "value": 0,
                "count": duration_4_less.count() + duration_4_7_bet.count() + duration_7_20_bet.count() + duration_20_plus.count()
            },
            {
                "label": "Less than 4 hours",
                "value": "4",
                "count": duration_4_less.count()
            },
            {
                "label": "4 - 7 hours ",
                "value": "4-7",
                "count": duration_4_7_bet.count()
            },
            {
                "label": "7 - 20 hours",
                "value": "7-20",
                "count": duration_7_20_bet.count()
            },
            {
                "label": "20 + hours",
                "value": "20",
                "count": duration_20_plus.count()
            },
        ]
        return data

    def get_queryset(self):
        """
        Method to get queryset for course.
        """
        subquery = CourseChapter.objects.filter(
            course__id=OuterRef('id')
        ).values('course__id').annotate(
            total_duration=Sum('chappter_lesson__duration')
        ).values('total_duration')[:1]

        course = Courses.objects.filter(course_status="PUBLISHED").annotate(
            rating=Coalesce(Avg("course_rating__rating"), 0, output_field=FloatField()),
            duration=Subquery(subquery)
        ).order_by("created_at")
        filter_course = self.filter_queryset(course)
        course_id = list(filter_course.values_list("id", flat=True))
        data = {
            "category": self.get_category(course_id),
            "rating": self.get_rating(course_id),
            "seller": self.get_seller(course_id),
            "duration": self.get_duration(course_id),
        }
        return data

    def get(self, request, *args, **kwargs):
        """
        GET Method for getting course list.
        """
        course_serializer = self.get_queryset()

        self.response_format["data"] = course_serializer
        self.response_format["error"] = None
        self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
        self.response_format["message"] = [messages.SUCCESS]
        return Response(self.response_format, status=self.status_code)


class ChapterListAPIView(DynamicFieldsViewMixin, ListAPIView):
    """
    Class for creating api for listing chapters.
    """
    permission_classes = [(IsAuthenticated & IsTokenValid & IsActiveUserPermission) | AllowAny]
    authentication_classes = (JWTAuthentication,)
    serializer_class = RetrieveChapterSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ("course",)
    ordering_fields = ("order_no",)

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(ChapterListAPIView, self).__init__(**kwargs)

    def paginate_queryset(self, queryset):
        """
        Method for get paginated query set.
        """
        pagination = self.request.GET.get("pagination", "False")
        if pagination == "True" or pagination == "true":
            return super().paginate_queryset(queryset)
        return None

    def get_queryset(self):
        """
        Method to get queryset for course.
        """
        return CourseChapter.objects.all()

    def get_serializer_context(self):
        """
        Method to get serializer context.
        """
        if self.request.user.is_authenticated:
            return {
                "request": self.request
            }
        return {}

    def get(self, request, *args, **kwargs):
        """
        GET Method for getting chapter list.
        """
        chapter_serializer = super().list(request, *args, **kwargs)

        self.response_format["data"] = chapter_serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
        self.response_format["message"] = [messages.SUCCESS]
        return Response(self.response_format, status=self.status_code)


class LessonListAPIView(DynamicFieldsViewMixin, ListAPIView):
    """
    Class for creating api for listing lessons.
    """
    permission_classes = [(IsAuthenticated & IsTokenValid & IsActiveUserPermission) | AllowAny]  # TODO: Add permission for access lesson video
    authentication_classes = (JWTAuthentication,)
    serializer_class = RetrieveLessonSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ("chapter",)
    ordering_fields = ("order_no",)

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(LessonListAPIView, self).__init__(**kwargs)

    def paginate_queryset(self, queryset):
        """
        Method for get paginated query set.
        """
        pagination = self.request.GET.get("pagination", "False")
        if pagination == "True" or pagination == "true":
            return super().paginate_queryset(queryset)
        return None

    def get_queryset(self):
        """
        Method to get queryset for lessons.
        """
        return CourseLesson.objects.all()

    def get(self, request, *args, **kwargs):
        """
        GET Method for getting lessons list.
        """
        lesson_serializer = super().list(request, *args, **kwargs)

        self.response_format["data"] = lesson_serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
        self.response_format["message"] = [messages.SUCCESS]
        return Response(self.response_format, status=self.status_code)
