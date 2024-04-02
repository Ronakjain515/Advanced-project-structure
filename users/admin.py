from django.contrib import admin

from .models import (
                     CustomUser,
                     RolesPermission,
                    )


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email")
    list_filter = ("role_permission", )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(RolesPermission)
