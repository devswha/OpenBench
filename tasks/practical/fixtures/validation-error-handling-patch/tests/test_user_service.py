import pytest

from user_service import create_user


def test_blank_email_raises() -> None:
    with pytest.raises(ValueError):
        create_user("   ", "Ada")


def test_email_is_trimmed() -> None:
    user = create_user("  ada@example.com  ", " Ada ")
    assert user == {"email": "ada@example.com", "name": "Ada"}
