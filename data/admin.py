from django.contrib import admin

from .models import Datasource


@admin.register(Datasource)
class DatasourceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "datasource_type",
        "organization",
        "created_by",
        "is_public",
        "created_at",
    )
    search_fields = ("name", "storage_url")
    list_filter = ("datasource_type", "organization", "is_public", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("organization", "created_by")
