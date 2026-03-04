from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization
from accounts.models import User


class Project(models.Model):
    """
    Geographic project container that belongs to an organization.
    Contains layers representing spatial data.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="projects"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects"
    )
    geometry = gis_models.GeometryField(
        null=True,
        blank=True,
        help_text="Bounding box or extent of the project"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["created_by"]),
        ]
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.name} @ {self.organization.name}"


class Layer(models.Model):
    """
    Contextual representation of a datasource within a project.
    Multiple layers can reference the same datasource with different styles/visibility.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="layers"
    )
    datasource = models.ForeignKey(
        "data.Datasource",
        on_delete=models.CASCADE,
        related_name="layers"
    )
    visibility = models.BooleanField(default=True)
    z_index = models.IntegerField(default=0, help_text="Layer stacking order (higher = on top)")
    style_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="MapLibre GL style configuration for this layer"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata/properties"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["z_index", "name"]
        indexes = [
            models.Index(fields=["project", "z_index"]),
            models.Index(fields=["datasource"]),
        ]
        verbose_name_plural = "Layers"

    def __str__(self):
        return f"{self.name} ({self.datasource.name})"
