from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization
from accounts.models import User


class Datasource(models.Model):
    """
    Spatial data source that can be used across multiple projects.
    Supports vector, raster, PMTiles, and MVT data types.
    """

    class Type(models.TextChoices):
        VECTOR = "vector", _("Vector")
        RASTER = "raster", _("Raster")
        PMTILES = "pmtiles", _("PMTiles")
        MVT = "mvt", _("Mapbox Vector Tiles")

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="datasources"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_datasources"
    )
    datasource_type = models.CharField(
        max_length=20,
        choices=Type.choices,
    )
    storage_url = models.CharField(
        max_length=500,
        help_text="URL or path to data source (GeoJSON, GeoTIFF, PMTiles, etc.)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data source metadata: projection, geometry_type, attributes, etc."
    )
    is_public = models.BooleanField(default=False, help_text="Accessible to all org members")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["datasource_type"]),
            models.Index(fields=["created_by"]),
        ]
        verbose_name_plural = "Datasources"

    def __str__(self):
        return f"{self.name} ({self.get_datasource_type_display()})"
