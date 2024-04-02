from random import random

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from utilities.mixins import CustomModelMixin
from django.utils.text import slugify


class RolesPermission(models.Model):
    """
    Class for creating model for storing Roles and Permissions details.
    """

    role_name = models.CharField(max_length=200, null=False, blank=False)
    role_type = models.JSONField(null=False, blank=False)
    permission_policy = models.JSONField(null=True, blank=False)
    created_at = models.DateTimeField(auto_now_add=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)

    def __str__(self):
        """
        Function to return email.
        """
        return self.role_name


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Class for creating model for storing Custom users.
    """
    Status_Choice = (
        ("ACTIVE", "Active"),
        ("INVITED", "Invited"),
        ("INACTIVE", "Inactive"),
    )
    Gender_Choices = (
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHERS", "Others"),
    )

    first_name = models.CharField(max_length=200, null=False, blank=False)
    last_name = models.CharField(max_length=200, null=False, blank=False)
    email = models.EmailField(_('email address'), unique=True, null=False, blank=False, error_messages={'unique': 'This email address is already associated with another account.'})
    status = models.CharField(max_length=10, null=False, blank=False, choices=Status_Choice)
    role_permission = models.ForeignKey(RolesPermission, null=True, blank=False, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        """
        Function to return email.
        """
        return str(self.email)


class BlackListedToken(models.Model):
    """
    Class for creating blacklisted tokens which have already been used.
    """
    token = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Class container containing information of the model.
        """
        unique_together = ("token",)


class SellerProfile(CustomModelMixin):
    """
    Class for creating seller profile model.
    """
    user = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE, related_name="seller_user")
    slug_name = models.SlugField(max_length=500, null=False, blank=False, unique=True)
    designation = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(null=True, blank=False)
    facebook_link = models.CharField(max_length=2000, null=True, blank=False)
    twitter_link = models.CharField(max_length=2000, null=True, blank=False)
    instagram_link = models.CharField(max_length=2000, null=True, blank=False)
    linkedin_link = models.CharField(max_length=2000, null=True, blank=False)

    def save(self, *args, **kwargs):
        if self.pk:
            number = self.slug_name.split("-")[::-1]
            self.slug_name = slugify(f"{self.user.first_name}-{self.user.last_name}-{number[0]}")
        else:
            self.slug_name = slugify(f"{self.user.first_name}-{self.user.last_name}-{random.randint(1,999)}")
        super().save(*args, **kwargs)
