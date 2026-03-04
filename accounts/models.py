from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending AbstractUser.
    Supports email-based authentication and profile extensions.
    """
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # switch authentication from username to email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-created_at"]
        # unique=True on email already creates an index; we only need
        # an explicit index on username if it's used for lookups.
        indexes = [
            models.Index(fields=["username"]),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.email})"
