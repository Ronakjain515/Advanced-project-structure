from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from common.models import CourseCategory, SubCourseCategory
from common.serializers import RetrieveCourseCategorySerializer, RetrieveCourseSubCategorySerializer
from utilities import messages
from utilities.mixins import DynamicFieldsViewMixin
from utilities.utils import ResponseInfo


class GetCourseCategoryListAPIView(DynamicFieldsViewMixin, ListAPIView):
    """
    Class for creating api for getting course Category list.
    """
    permission_classes = ()
    authentication_classes = ()
    serializer_class = RetrieveCourseCategorySerializer

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(GetCourseCategoryListAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        Method for getting course Category queryset.
        """
        return CourseCategory.objects.all().annotate(
            value=F("id")
        ).order_by("name")

    def get(self, request, *args, **kwargs):
        """
        GET Method for getting course Category list.
        """
        category_serializer = super().list(request, *args, **kwargs)

        self.response_format["data"] = category_serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
        self.response_format["message"] = [messages.SUCCESS]
        return Response(self.response_format, status=self.status_code)


class GetCourseSubCategoryListAPIView(DynamicFieldsViewMixin, ListAPIView):
    """
    Class for creating api for getting course sub-Category list.
    """
    permission_classes = ()
    authentication_classes = ()
    serializer_class = RetrieveCourseSubCategorySerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = ("category",)

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(GetCourseSubCategoryListAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        Method for getting course sub-Category queryset.
        """
        return SubCourseCategory.objects.all().annotate(
            category_name=F("category__name"),
            value=F("id"),
        ).order_by("name")

    def get(self, request, *args, **kwargs):
        """
        GET Method for getting course sub-Category list.
        """
        category_serializer = super().list(request, *args, **kwargs)

        self.response_format["data"] = category_serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
        self.response_format["message"] = [messages.SUCCESS]
        return Response(self.response_format, status=self.status_code)
