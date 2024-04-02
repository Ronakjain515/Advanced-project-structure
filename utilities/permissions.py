from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission

from . import messages
from users.models import BlackListedToken


class IsTokenValid(BasePermission):
    """
    Class for validating if the token is present in the blacklisted token list.
    """
    message = 'You do not have permission.'

    def has_permission(self, request, view):
        """
        Function for checking if the caller of this function has
         permission to access particular API.
        """
        is_allowed_user = True
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            key, token = auth_header.split(' ')
            if key == 'Bearer':
                try:
                    is_blacklisted = BlackListedToken.objects.get(token=token)
                    if is_blacklisted:
                        is_allowed_user = False
                except BlackListedToken.DoesNotExist:
                    is_allowed_user = True
        else:
            is_allowed_user = False
        return is_allowed_user


class IsActiveUserPermission(BasePermission):
    """
    Class for specifying the details can only be manipulated by the users himself.
    """
    message = 'You do not have permission.'

    def has_permission(self, request, view):
        """
        Function for checking if caller's users is active.
        """
        return request.user.status in ["ACTIVE", "INVITED"]


class CustomPermissionException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "You do not have permission to perform this action."

    def __init__(self, detail=None):
        """
        Method to display custom exception message
        """
        if detail is not None:
            self.detail = detail
        else:
            self.detail = self.default_detail


class IsSuperAdminPermission(BasePermission):
    """
    Class for specifying the details are manipulated by super admin.
    """

    message = messages.PERMISSION_DENIED

    def has_permission(self, request, view):
        """
        Function for checking if users is active.
        """
        return "SUPER_ADMIN" in request.user.role_permission.role_type


class IsSellerPermission(BasePermission):
    """
    Class for specifying the details are manipulated by Seller.
    """

    message = messages.PERMISSION_DENIED

    def has_permission(self, request, view):
        """
        Function for checking if users is active.
        """
        return "SELLER" in request.user.role_permission.role_type


class IsObjectOwnerPermission(BasePermission):
    """
    Class for specifying the details are manipulated by owner itself.
    """

    message = messages.PERMISSION_DENIED

    def has_object_permission(self, request, view, obj):
        """
        Function for checking if users is active.
        """
        return obj.created_by.id == request.user.id
