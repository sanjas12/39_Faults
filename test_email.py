from app.services.email_service import email_service


def test_email():
    result = email_service._send_email(
        to_email="test@example.com",
        subject="Тестовое письмо",
        html_content="<h1>Тест!</h1><p>Это тестовое письмо из системы Faults</p>",
    )
    print(f"Результат: {result}")


if __name__ == "__main__":
    test_email()
