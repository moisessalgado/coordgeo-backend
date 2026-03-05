from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from data.models import Datasource
from organizations.models import Membership, Organization
from projects.models import Layer, Project


class Command(BaseCommand):
    help = "Seed idempotent integration data for frontend-backend smoke tests"

    @transaction.atomic
    def handle(self, *args, **options):
        demo_user, _ = User.objects.get_or_create(
            email="demo@coordgeo.local",
            defaults={
                "username": "demo",
                "first_name": "Demo",
                "last_name": "User",
                "is_active": True,
            },
        )
        demo_user.set_password("Passw0rd!")
        demo_user.save(update_fields=["password", "updated_at"])

        outsider_user, _ = User.objects.get_or_create(
            email="outsider@coordgeo.local",
            defaults={
                "username": "outsider",
                "first_name": "Outsider",
                "last_name": "User",
                "is_active": True,
            },
        )
        outsider_user.set_password("Passw0rd!")
        outsider_user.save(update_fields=["password", "updated_at"])

        org, _ = Organization.objects.get_or_create(
            slug="demo-org",
            defaults={
                "name": "Demo Organization",
                "description": "Organização seed para integração frontend-backend",
                "org_type": Organization.OrgType.TEAM,
                "plan": Organization.Plan.FREE,
                "owner": demo_user,
            },
        )

        Membership.objects.get_or_create(
            user=demo_user,
            organization=org,
            defaults={"role": Membership.Role.ADMIN},
        )

        if org.owner_id != demo_user.id:
            org.owner = demo_user
            org.save(update_fields=["owner", "updated_at"])

        geometry = GEOSGeometry("POLYGON((-74 -34, -34 -34, -34 5, -74 5, -74 -34))", srid=4326)

        project, _ = Project.objects.get_or_create(
            name="Projeto Brasil Demo",
            organization=org,
            defaults={
                "description": "Projeto para smoke test integrado",
                "created_by": demo_user,
                "geometry": geometry,
            },
        )

        datasource, _ = Datasource.objects.get_or_create(
            name="OSM Raster Demo",
            organization=org,
            defaults={
                "description": "Datasource raster para smoke test",
                "created_by": demo_user,
                "datasource_type": Datasource.Type.RASTER,
                "storage_url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                "metadata": {"attribution": "© OpenStreetMap contributors"},
                "is_public": True,
            },
        )

        layer, _ = Layer.objects.get_or_create(
            name="Camada Raster OSM",
            project=project,
            datasource=datasource,
            defaults={
                "description": "Layer base para mapa",
                "visibility": True,
                "z_index": 1,
                "style_config": {
                    "type": "raster",
                    "paint": {"raster-opacity": 0.85},
                },
                "metadata": {},
            },
        )

        self.stdout.write(self.style.SUCCESS("Integration seed completed."))
        self.stdout.write(f"demo_email={demo_user.email}")
        self.stdout.write("demo_password=Passw0rd!")
        self.stdout.write(f"outsider_email={outsider_user.email}")
        self.stdout.write("outsider_password=Passw0rd!")
        self.stdout.write(f"organization_id={org.id}")
        self.stdout.write(f"project_id={project.id}")
        self.stdout.write(f"datasource_id={datasource.id}")
        self.stdout.write(f"layer_id={layer.id}")
