#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from organizations.views import OrganizationViewSet

# Check if create_team action exists
if hasattr(OrganizationViewSet, 'create_team'):
    print("✓ create_team action found in OrganizationViewSet")
    # Check if it has the action decorator
    create_team_func = getattr(OrganizationViewSet, 'create_team')
    if hasattr(create_team_func, 'mapping'):
        print(f"✓ create_team has DRF action decorator")
        print(f"  Mapping: {create_team_func.mapping}")
    else:
        print("✗ create_team does NOT have DRF action decorator properly applied")
else:
    print("✗ create_team action NOT found in OrganizationViewSet")

# List all actions
print("\nAll ViewSet actions:")
for attr_name in dir(OrganizationViewSet):
    attr = getattr(OrganizationViewSet, attr_name)
    if hasattr(attr, 'mapping'):
        print(f"  - {attr_name}: {attr.mapping}")
