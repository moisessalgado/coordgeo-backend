from django.contrib import admin

from .models import Project, Layer


# ---------------------------------------------------------------------------
# Project admin
# ---------------------------------------------------------------------------
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization",
        "created_by",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "organization__name", "created_by__username")
    list_filter = ("organization", "created_by", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("organization", "created_by")


# ---------------------------------------------------------------------------
# Layer admin
# ---------------------------------------------------------------------------
@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "project",
        "datasource",
        "visibility",
        "z_index",
        "created_at",
    )
    search_fields = ("name", "project__name", "datasource__name")
    list_filter = ("visibility", "project")
    ordering = ("z_index",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("project", "datasource")
