from django.db.models import F, Avg, Q, FloatField
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    RetrieveAPIView,
)
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)
from rest_framework_simplejwt.authentication import JWTAuthentication

from .filters import SellerFilter
from .models import (
    CustomUser,
    SellerProfile,
)

from utilities.utils import get_tokens_for_user, CustomPagination

from .serializers import (
    UserLoginSerializer,
    RolePermissionSerializer,
    RetrieveSellerSerializer,
    ChangeCustomUserSerializer,
    ChangeSellerProfileSerializer,
)
from utilities.permissions import (
    IsTokenValid,
    IsActiveUserPermission,
    IsObjectOwnerPermission,
)
from utilities.mixins import DynamicFieldsViewMixin

from .models import RolesPermission
from utilities import messages
from utilities.utils import ResponseInfo


class CreateBuyerUserAPIView(CreateAPIView):
    """
    Class for creating api for creating buyer users.
    """
    permission_classes = ()
    authentication_classes = ()
    serializer_class = ChangeCustomUserSerializer

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CreateBuyerUserAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        POST Method for creating buyer users.
        """
        buyer_role = RolesPermission.objects.filter(role_type__contains="BUYER").first()
        request.data["role_permission"] = buyer_role.id
        user_serializer = self.get_serializer(data=request.data)
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()

            response_data = user_serializer.data
            response_data["profile_image_key"] = None
            self.response_format["data"] = response_data
            self.response_format["error"] = None
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["message"] = [messages.CREATION.format("User")]
        return Response(self.response_format)


class LoginAPIView(CreateAPIView):
    """
    Class for creating api for login users.
    """
    permission_classes = ()
    authentication_classes = ()
    serializer_class = UserLoginSerializer

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(LoginAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        POST Method for validating and logging in the users if valid.
        """
        try:
            email = request.data.get("email")
            if email:
                user = CustomUser.objects.get(email=email)
                user_type = request.data.get("role")

                if user_type:
                    user_serializer = self.get_serializer(data=request.data, context={"role": user_type})

                    if user_serializer.is_valid(raise_exception=True):
                        jwt_token = get_tokens_for_user(user)
                        if user.status == "INVITED" and ("STUDENT" in user.role_permission.role_type or "MENTOR" in user.role_permission.role_type):
                            user.status = "ACTIVE"
                            user.save()

                        role_permission_serializer = RolePermissionSerializer(user.role_permission, many=False)

                        data = {
                            "id": user.id,
                            "token": jwt_token,
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "status": user.status,
                            "date_joined": user.date_joined,
                            "role_permission": role_permission_serializer.data,
                        }

                        if role_permission_serializer.data.get("role_type")[0] == "SELLER":
                            seller_obj = SellerProfile.objects.get(user=user.id)
                            if seller_obj.slug_name:
                                data["slug_name"] = seller_obj.slug_name

                        self.response_format["data"] = data
                        self.response_format["error"] = None
                        self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
                        self.response_format["message"] = [messages.LOGIN_SUCCESS]
                else:
                    self.response_format["data"] = None
                    self.response_format["error"] = "role"
                    self.response_format["status_code"] = self.status_code = status.HTTP_400_BAD_REQUEST
                    self.response_format["message"] = [messages.REQUIRED_FIELD]
            else:
                self.response_format["data"] = None
                self.response_format["error"] = "email"
                self.response_format["status_code"] = self.status_code = status.HTTP_400_BAD_REQUEST
                self.response_format["message"] = [messages.REQUIRED_FIELD]
        except CustomUser.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["error"] = "users"
            self.response_format["status_code"] = self.status_code = status.HTTP_404_NOT_FOUND
            self.response_format["message"] = [messages.UNAUTHORIZED_ACCOUNT]
        return Response(self.response_format, self.status_code)


class CreateSellerUserAPIView(CreateAPIView):
    """
    Class for creating api for creating seller users.
    """
    permission_classes = ()
    authentication_classes = ()
    serializer_class = ChangeCustomUserSerializer

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CreateSellerUserAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        POST Method for creating seller users.
        """
        buyer_role = RolesPermission.objects.filter(role_type__contains="SELLER").first()
        request.data["role_permission"] = buyer_role.id
        user_serializer = self.get_serializer(data=request.data)
        if user_serializer.is_valid(raise_exception=True):
            seller_profile_serializer = ChangeSellerProfileSerializer(data=request.data)
            if seller_profile_serializer.is_valid(raise_exception=True):
                user = user_serializer.save()
                seller_profile_serializer.save(user=user, created_by=user, updated_by=user)

            self.response_format["data"] = user_serializer.data
            self.response_format["error"] = None
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["message"] = [messages.CREATION.format("Seller Account")]
        return Response(self.response_format)


class GetSellerListAPIView(DynamicFieldsViewMixin, ListAPIView):
    """
    Class for creating api for getting seller list.
    """
    permission_classes = [(IsAuthenticated & IsTokenValid & IsActiveUserPermission) | AllowAny]
    authentication_classes = (JWTAuthentication,)
    serializer_class = RetrieveSellerSerializer
    pagination_class = CustomPagination
    filterset_class = SellerFilter

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(GetSellerListAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """migration
        Method to get seller queryset.
        """
        return SellerProfile.objects.all().annotate(
            user_first_name=F("user__first_name"),
            user_last_name=F("user__last_name"),
            rating=Coalesce(Avg("user__course_seller__course_rating__rating", filter=Q(user__course_seller__course_status="PUBLISHED")), 0, output_field=FloatField()),
        )

    def paginate_queryset(self, queryset):
        """
        Method for get paginated query set.
        """
        pagination = self.request.GET.get("pagination", "False")
        if pagination == "True" or pagination == "true":
            return super().paginate_queryset(queryset)
        return None

    def get(self, request, *args, **kwargs):
        """
        GET Method for getting seller list.
        """
        seller_serializer = super().list(request, *args, **kwargs)

        self.response_format["data"] = seller_serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
        self.response_format["message"] = [messages.SUCCESS]
        return Response(self.response_format, status=self.status_code)


class GetSellerDetailsAPIView(DynamicFieldsViewMixin, RetrieveAPIView):
    """
    Class for creating api for getting seller details.
    """
    permission_classes = [(IsAuthenticated & IsTokenValid & IsActiveUserPermission) | AllowAny]
    authentication_classes = (JWTAuthentication,)
    serializer_class = RetrieveSellerSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(GetSellerDetailsAPIView, self).__init__(**kwargs)

    def get_serializer_context(self):
        """
        Method to get context for serializer
        """
        return {
            "is_course": True
        }

    def get_queryset(self):
        """
        Method to get seller queryset.
        """
        return SellerProfile.objects.annotate(
            user_first_name=F("user__first_name"),
            user_last_name=F("user__last_name"),
            user_email=F("user__email"),
        ).get(slug_name=self.kwargs["slug"])

    def get(self, request, *args, **kwargs):
        """
        GET Method for getting seller details.
        """
        try:
            seller_obj = self.get_queryset()
            seller_serializer = self.get_serializer(seller_obj, many=False)

            self.response_format["data"] = seller_serializer.data
            self.response_format["error"] = None
            self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
            self.response_format["message"] = [messages.SUCCESS]
        except SellerProfile.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["error"] = "Seller"
            self.response_format["status_code"] = self.status_code = status.HTTP_400_BAD_REQUEST
            self.response_format["message"] = [messages.DOES_NOT_EXISTS.format("Seller")]
        return Response(self.response_format, status=self.status_code)


class UpdateSellerDetailsAPIView(UpdateAPIView):
    """
    Class for creating api for updating seller details.
    """
    permission_classes = [(IsAuthenticated & IsTokenValid & IsActiveUserPermission & IsObjectOwnerPermission)]
    authentication_classes = (JWTAuthentication,)
    serializer_class = ChangeSellerProfileSerializer

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.status_code = status.HTTP_200_OK
        self.response_format = ResponseInfo().response
        super(UpdateSellerDetailsAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        Method to get seller queryset.
        """
        return SellerProfile.objects.get(slug_name=self.kwargs["slug"])

    def patch(self, request, *args, **kwargs):
        """
        PATCH Method for updating seller details.
        """
        try:
            seller_obj = self.get_queryset()

            self.check_object_permissions(request, seller_obj)

            seller_serializer = self.get_serializer(seller_obj, data=request.data, partial=True)
            seller_user_serializer = ChangeCustomUserSerializer(seller_obj.user, data=request.data, partial=True)
            if seller_serializer.is_valid(raise_exception=True):
                if seller_user_serializer.is_valid(raise_exception=True):
                    self.perform_update(seller_user_serializer)
                    self.perform_update(seller_serializer)

            response_data = seller_serializer.data
            response_data["slug_name"] = seller_obj.slug_name
            response_data["users"] = seller_user_serializer.data

            self.response_format["data"] = response_data
            self.response_format["error"] = None
            self.response_format["status_code"] = self.status_code = status.HTTP_200_OK
            self.response_format["message"] = [messages.SUCCESS]
        except SellerProfile.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["error"] = "Seller"
            self.response_format["status_code"] = self.status_code = status.HTTP_400_BAD_REQUEST
            self.response_format["message"] = [messages.DOES_NOT_EXISTS.format("Seller")]
        return Response(self.response_format, status=self.status_code)
