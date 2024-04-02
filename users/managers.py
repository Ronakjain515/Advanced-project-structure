"""
This file is used for creating custom users manager for the correspondent custom users.
"""
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Class for creating custom manager for managing custom users.
    """
    def create_user(self, email=None, first_name=None, last_name=None, password=None, status="ACTIVE", phone=None,
                    role_permission=None, date_joined=None, **extra_fields):
        """
        Function for creating users w.r.t custom users.
        """
        user = self.model(
            email=self.normalize_email(email) if self.normalize_email(email) != "" else None,
            **extra_fields
        )
        user.first_name = first_name
        user.last_name = last_name
        user.status = status
        user.is_superuser = False
        user.is_active = True
        user.is_staff = False
        user.role_permission = role_permission
        user.date_joined = date_joined
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, email, password, last_name):
        """
        Function for creating superuser.
        """
        user = self.create_user(
            email,
            first_name,
            last_name,
            password,
            status='ACTIVE',
            date_joined=timezone.now()
        )
        user.is_superuser = True
        user.is_active = True
        user.is_staff = True
        user.save(using=self._db)
        return user
