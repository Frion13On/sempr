import pytest

from api import users_api


def test_validate_teacher_payload_success():
    ok, error, filtered = users_api._validate_and_filter_user_payload(
        "преподаватели",
        {
            "фио_преп": "Иванов И.И.",
            "логин": "teacher01",
            "пароль": "StrongPass!",
            "телефон": "89001234567",
            "почта": "teacher@example.com",
            "неизвестное": "ignored",
        },
    )

    assert ok is True
    assert error is None
    assert set(filtered.keys()) == {
        "фио_преп",
        "логин",
        "пароль",
        "телефон",
        "почта",
    }


def test_validate_payload_missing_required():
    ok, error, filtered = users_api._validate_and_filter_user_payload(
        "студенты",
        {
            "фио_студ": "",
            "логин": "student01",
            "пароль": "student01",  # также нарушает правило
        },
    )

    assert ok is False
    assert "обязательно" in error
    assert filtered is None


@pytest.mark.parametrize(
    "payload,error_msg",
    [
        (
            {"фио_преп": "Иванов", "логин": "t", "пароль": "t"},
            "Логин и пароль не должны совпадать",
        ),
        (
            {
                "фио_преп": "Иванов",
                "логин": "teacher02",
                "пароль": "secret",
                "телефон": "123-456",
            },
            "Телефон",
        ),
        (
            {
                "фио_преп": "Иванов",
                "логин": "teacher03",
                "пароль": "secret",
                "почта": "invalid-email",
            },
            "email",
        ),
    ],
)
def test_validate_payload_invalid_values(payload, error_msg):
    ok, error, filtered = users_api._validate_and_filter_user_payload(
        "преподаватели",
        payload,
    )

    assert ok is False
    assert error_msg in error
    assert filtered is None


def test_validate_payload_rejects_malicious_input():
    ok, error, filtered = users_api._validate_and_filter_user_payload(
        "преподаватели",
        {
            "фио_преп": "<script>alert(1)</script>",
            "логин": "teacher04",
            "пароль": "secret",
        },
    )

    assert ok is False
    assert "опасный" in error
    assert filtered is None

