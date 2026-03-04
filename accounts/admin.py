from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin for custom User model."""

    list_display = (
        "id",
        "email",
        "username",
        "is_active",
        "created_at",
        "updated_at",
    )
    search_fields = ("email", "username")
    list_filter = ("is_active",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    # no foreign keys here
