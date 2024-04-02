import django_filters
from django.utils.dateparse import parse_duration

from .models import Courses
from utilities.constants import DurationTypes


class CourseFilter(django_filters.FilterSet):
    """
    Class to filter course list api
    """
    category = django_filters.CharFilter(method="filter_category")
    subcategory = django_filters.CharFilter(method="filter_subcategory")
    rating = django_filters.NumberFilter(method="filter_rating")
    seller = django_filters.CharFilter(method="filter_seller")
    duration = django_filters.CharFilter(method="filter_duration")

    def filter_category(self, queryset, _name, value):
        """
        function to filter course category
        """
        category = value.split(",")
        return queryset.filter(category__in=category)

    def filter_subcategory(self, queryset, _name, value):
        """
        function to filter course sub category
        """
        subcategory = value.split(",")
        return queryset.filter(sub_category__in=subcategory)

    def filter_seller(self, queryset, _name, value):
        """
        function to filter course seller
        """

        seller = value.split(",")
        return queryset.filter(seller__in=seller)

    def filter_rating(self, queryset, _name, value):
        """
        function to filter course rating
        """
        return queryset.filter(rating__gte=value)

    def filter_duration(self, queryset, _name, value):
        """
        function to filter course duration
        """
        duration = DurationTypes.get(value)
        if duration and duration.get("min"):
            min_duration = parse_duration(duration.get("min"))
            queryset = queryset.filter(duration__gte=min_duration)
        if duration and duration.get("max"):
            max_duration = parse_duration(duration.get("max"))
            queryset = queryset.filter(duration__lte=max_duration)

        return queryset

    class Meta:
        model = Courses
        fields = ("category", "subcategory", "seller", "rating", "duration")

