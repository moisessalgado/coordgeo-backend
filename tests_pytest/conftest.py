import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user_factory(db):
    user_model = get_user_model()

    def factory(*, username: str, email: str, password: str = "testpass123"):
        return user_model.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

    return factory
