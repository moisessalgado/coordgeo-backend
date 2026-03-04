from django.contrib import admin

from .models import Permission


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "resource_type",
        "resource_id",
        "subject_user",
        "subject_team",
        "role",
        "granted_by",
        "granted_at",
    )
    search_fields = (
        "resource_type",
        "role",
        "subject_user__email",
        "subject_team__name",
    )
    list_filter = ("resource_type", "role", "granted_at")
    ordering = ("-granted_at",)
    readonly_fields = ("granted_at", "updated_at")
    list_select_related = ("subject_user", "subject_team", "granted_by")
