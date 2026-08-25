def test_operator_cannot_create_project(client, auth_headers):
    """Оператор не может создать проект"""
    response = client.post(
        "/api/projects/",
        json={"name": "Проект от оператора", "description": "Описание"},
        headers=auth_headers,
    )

    assert response.status_code == 403


def test_engineer_can_create_project(client, engineer_headers):
    """Инженер может создать проект"""
    response = client.post(
        "/api/projects/",
        json={
            "name": "Проект от инженера",
            "description": "Описание",
            "client": "Клиент",
        },
        headers=engineer_headers,
    )

    assert response.status_code == 201


def test_operator_can_view_projects(client, auth_headers, test_project):
    """Оператор может просматривать проекты"""
    response = client.get("/api/projects/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_admin_can_delete_any_project(client, admin_headers, test_project):
    """Администратор может удалить любой проект"""
    # Добавляем фикстуру admin_headers в conftest.py
    response = client.delete(f"/api/projects/{test_project.id}", headers=admin_headers)

    assert response.status_code == 204
