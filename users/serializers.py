from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import (
    CustomUser,
    SellerProfile,
    RolesPermission,
)
from courses.models import (
    Courses,
    CourseRatings,
    EnrolledCourses,
)
from utilities.mixins import DynamicFieldsSerializerMixin


class ChangeCustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer class for adding and updating custom users.
    """
    class Meta:
        model = CustomUser
        fields = ("id", "first_name", "last_name", "email", "password", "role_permission", "date_joined",)
        extra_kwargs = {
            "role_permission": {"required": True},
            "phone": {"required": True},
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        """
        Function for creating and returning the created instance
         based on the validated data of the users.
        """
        user = CustomUser.objects.create_user(
            first_name=validated_data.pop('first_name'),
            last_name=validated_data.pop('last_name'),
            email=validated_data.pop('email'),
            password=validated_data.pop('password'),
            role_permission=validated_data.pop('role_permission')
        )
        return user


class RetrieveCustomUserSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for retrieving data of custom users or buyer
    """
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "status", "is_active")


class UserLoginSerializer(serializers.Serializer):
    """
    Class for authorizing users for correct login credentials.
    """
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    default_error_messages = {
        'inactive_account': 'User account is {}.',
        'invalid_credentials': 'Email address or password is invalid.',
        'wrong_platform': 'You are not authorised to login this platform.'
    }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate(self, attrs):
        """
        Function for validating and returning the created instance
         based on the validated data of the users.
        """
        user = authenticate(username=attrs.pop("email"), password=attrs.pop('password'))

        if user:
            if not (
                    (self.context["role"] == "USER" and ("BUYER" in user.role_permission.role_type or "SELLER" in user.role_permission.role_type))
                    or (self.context["role"] == "SUPER_ADMIN" and "SUPER_ADMIN" in user.role_permission.role_type)
                    # or (self.context["role"] == "MENTOR" and ("MENTOR" in users.role_permission.role_type))
            ):
                raise serializers.ValidationError(self.error_messages['wrong_platform'])
            if not (user.status in ["ACTIVE", "INVITED"]):
                raise serializers.ValidationError(self.error_messages['inactive_account'].format(user.status.title()))
            return attrs
        else:
            raise serializers.ValidationError(self.error_messages['invalid_credentials'])


class RolePermissionSerializer(serializers.ModelSerializer):
    """
    Serializer class for role and permission model.
    """
    class Meta:
        """
        Class container containing information of the model.
        """
        model = RolesPermission
        fields = ("id", "role_name", "permission_policy", "role_type", "created_at", "updated_at")


class ChangeSellerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer class for adding and updating Seller Profile.
    """
    class Meta:
        model = SellerProfile
        fields = ("id", "users", "designation", "description", "facebook_link", "twitter_link", "instagram_link",
                  "linkedin_link", "created_at", "updated_at", "created_by", "updated_by", "is_deleted")
        extra_kwargs = {
            "created_by": {"required": False},
            "updated_by": {"required": False},
            "users": {"required": False},
        }

    def update(self, instance, validated_data):
        # Exclude certain fields from being updated after creation
        if 'users' in validated_data:
            del validated_data['users']
        if 'created_by' in validated_data:
            del validated_data['created_by']

        # Custom logic for updating a users
        user = super().update(instance, validated_data)
        # Additional logic if needed
        return user


class RetrieveSellerSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    """
    Serializer class for retrieving data of sellers.
    """
    user_first_name = serializers.CharField(read_only=True)
    user_last_name = serializers.CharField(read_only=True)
    user_email = serializers.CharField(read_only=True)
    ratings = serializers.SerializerMethodField(read_only=True)
    student_count = serializers.SerializerMethodField(read_only=True)
    courses_count = serializers.SerializerMethodField(read_only=True)
    courses = serializers.SerializerMethodField(read_only=True)
    seller_id = serializers.SerializerMethodField(read_only=True)

    def get_seller_id(self, obj):
        """
        Method to get seller id.
        """
        return obj.user.id

    def get_ratings(self, obj):
        """
        Method to get ratings.
        """
        reviews = CourseRatings.objects.filter(course__seller=obj.user.id, course__course_status="PUBLISHED").order_by("-created_at")

        list_stars_rating = list(reviews.values_list("rating", flat=True))
        sum_of_rating_star = sum(list_stars_rating)
        length_of_rating_star = len(list_stars_rating)
        if length_of_rating_star > 0:
            total_rating = round(sum_of_rating_star / length_of_rating_star, 2)
        else:
            total_rating = 0

        return {
            "total_rating": total_rating,
            "total_reviews_count": length_of_rating_star,
        }

    def get_student_count(self, obj):
        """
        Method to get student count.
        """
        return EnrolledCourses.objects.filter(course__seller__id=obj.user.id).count()

    def get_courses_count(self, obj):
        """
        Method to get courses count.
        """
        return Courses.objects.filter(course_status="PUBLISHED", seller=obj.user.id).count()

    def get_courses(self, obj):
        """
        Method to get courses.
        """
        courses = []
        if self.context.get("is_course"):
            courses = Courses.objects.filter(course_status="PUBLISHED", seller=obj.user.id).order_by("-created_at").values()
        return courses

    class Meta:
        model = SellerProfile
        fields = ("id", "seller_id", "designation", "user_first_name", "user_last_name", "user_email", "facebook_link", "instagram_link",
                  "slug_name", "linkedin_link", "twitter_link", "description", "ratings",
                  "student_count", "courses_count", "courses")

