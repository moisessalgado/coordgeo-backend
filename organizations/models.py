from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class Organization(models.Model):
    """
    Top-level container for multi-tenant data.
    Every user must belong to at least one organization (personal).
    """

    class OrgType(models.TextChoices):
        PERSONAL = "personal", _("Personal")
        TEAM = "team", _("Team")

    class Plan(models.TextChoices):
        FREE = "free", _("Free")
        PRO = "pro", _("Professional")
        ENTERPRISE = "enterprise", _("Enterprise")

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField(blank=True)
    org_type = models.CharField(
        max_length=20,
        choices=OrgType.choices,
        default=OrgType.PERSONAL,
    )
    plan = models.CharField(
        max_length=20,
        choices=Plan.choices,
        default=Plan.FREE,
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_organizations",
        help_text="Owner of this organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()})"

    def clean(self):
        # use TextChoices constants for comparisons
        if self.org_type == Organization.OrgType.PERSONAL and self.plan != Organization.Plan.FREE:
            raise ValidationError(_("Personal organizations must use the free plan."))


class Membership(models.Model):
    """
    Links users to organizations with specific roles.
    Controls access and permissions within an organization.
    """
    class Role(models.TextChoices):
        MEMBER = "member", _("Member")
        ADMIN = "admin", _("Admin")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="org_memberships"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members"
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "organization")
        ordering = ["-joined_at"]
        indexes = [
            models.Index(fields=["organization", "role"]),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.organization.name} ({self.role})"


class Team(models.Model):
    """
    Sub-groups within an organization.
    Teams can have multiple members and control access to projects/datasources.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="teams"
    )
    members = models.ManyToManyField(
        User,
        related_name="teams",
        blank=True,
        help_text="Members of this team"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization"]),
        ]

    def __str__(self):
        return f"{self.name} @ {self.organization.name}"
