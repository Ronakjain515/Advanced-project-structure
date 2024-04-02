import django_filters
from .models import SellerProfile


class SellerFilter(django_filters.FilterSet):
    """
    Class to filter seller list api
    """
    rating = django_filters.NumberFilter(method="filter_rating")

    def filter_rating(self, queryset, _name, value):
        """
        function to filter seller ratings
        """
        return queryset.filter(rating__gte=value)

    class Meta:
        model = SellerProfile
        fields = ["rating"]
