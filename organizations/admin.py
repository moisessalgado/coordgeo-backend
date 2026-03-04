from django.contrib import admin

from .models import Organization, Membership, Team


# ---------------------------------------------------------------------------
# Organization admin
# ---------------------------------------------------------------------------
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "org_type",
        "plan",
        "owner",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "slug")
    list_filter = ("org_type", "plan", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("owner",)


# ---------------------------------------------------------------------------
# Membership admin
# ---------------------------------------------------------------------------
@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "organization",
        "role",
        "joined_at",
    )
    search_fields = ("user__username", "organization__name")
    list_filter = ("role", "joined_at")
    ordering = ("-joined_at",)
    list_select_related = ("user", "organization")


# ---------------------------------------------------------------------------
# Team admin
# ---------------------------------------------------------------------------
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization",
        "created_at",
    )
    search_fields = ("name", "organization__name")
    list_filter = ("organization", "created_at")
    ordering = ("name",)
    list_select_related = ("organization",)
