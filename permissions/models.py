from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from organizations.models import Team


class Permission(models.Model):
    """
    Flexible Access Control List (ACL) for fine-grained permissions.
    Supports role-based access on different resource types.
    Either subject_user or subject_team must be set, not both.
    """

    class ResourceType(models.TextChoices):
        ORGANIZATION = "organization", _("Organization")
        PROJECT = "project", _("Project")
        DATASOURCE = "datasource", _("Datasource")

    class Role(models.TextChoices):
        VIEW = "view", _("View")
        EDIT = "edit", _("Edit")
        MANAGE = "manage", _("Manage")

    resource_type = models.CharField(max_length=50, choices=ResourceType.choices)
    resource_id = models.IntegerField(help_text="ID of the resource (org_id, project_id, etc.)")
    
    subject_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="perm_subjects"
    )
    subject_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="team_permissions"
    )
    
    role = models.CharField(max_length=20, choices=Role.choices)
    granted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="granted_permissions",
        help_text="User who granted this permission"
    )

    class Meta:
        ordering = ["-granted_at"]
        indexes = [
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["subject_user", "role"]),
            models.Index(fields=["subject_team", "role"]),
        ]
        verbose_name_plural = "Permissions"

    def clean(self):
        # Validate that either subject_user or subject_team is set, but not both
        if self.subject_user and self.subject_team:
            raise ValidationError(
                _("A permission must be granted to either a user or a team, not both.")
            )
        
        if not self.subject_user and not self.subject_team:
            raise ValidationError(
                _("A permission must be granted to either a user or a team.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        subject = self.subject_user or self.subject_team
        return f"{subject} → {self.get_resource_type_display()} #{self.resource_id} ({self.role})"
