def test_create_project(client, engineer_headers, test_user):
    """Тест создания проекта (требуются права ENGINEER)"""
    response = client.post(
        "/api/projects/",
        json={
            "name": "Новый тестовый проект",
            "description": "Описание нового проекта",
            "client": "Новый клиент",
            "station": "Новая станция",
            "unit": 2,
            "type": "САУ",
        },
        headers=engineer_headers,  # ✅ Используем инженера
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Новый тестовый проект"
    assert data["client"] == "Новый клиент"
    assert data["station"] == "Новая станция"


def test_list_projects(client, auth_headers, test_project):
    """Тест получения списка проектов"""
    response = client.get("/api/projects/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Тестовый проект"


def test_get_project(client, auth_headers, test_project):
    """Тест получения проекта по ID"""
    response = client.get(f"/api/projects/{test_project.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_project.id
    assert data["name"] == "Тестовый проект"


def test_update_project(client, engineer_headers, test_project):
    """Тест обновления проекта (требуются права ENGINEER)"""
    response = client.put(
        f"/api/projects/{test_project.id}",
        json={
            "name": "Обновлённый проект",
            "description": "Новое описание",
            "client": "Новый клиент",
        },
        headers=engineer_headers,  # ✅ Используем инженера
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Обновлённый проект"
    assert data["client"] == "Новый клиент"


def test_delete_project(client, engineer_headers, test_project):
    """Тест удаления проекта (требуются права ENGINEER)"""
    response = client.delete(
        f"/api/projects/{test_project.id}",
        headers=engineer_headers,  # ✅ Используем инженера
    )

    assert response.status_code == 204

    # Проверяем, что проект удалён
    get_response = client.get(
        f"/api/projects/{test_project.id}", headers=engineer_headers
    )
    assert get_response.status_code == 404


def test_get_project_stats(client, auth_headers, test_project, test_fault):
    """Тест получения статистики проекта"""
    response = client.get(
        f"/api/projects/{test_project.id}/stats", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == test_project.id
    assert data["total"] >= 1


def test_filter_projects_by_station(client, auth_headers, test_project):
    """Тест фильтрации проектов по станции"""
    response = client.get(
        f"/api/projects/?station={test_project.station}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(p["station"] == test_project.station for p in data)


def test_create_project_unauthorized(client, auth_headers):
    """Тест создания проекта без прав ENGINEER (должен вернуть 403)"""
    response = client.post(
        "/api/projects/",
        json={"name": "Проект без прав", "description": "Описание"},
        headers=auth_headers,  # ✅ Обычный пользователь
    )

    assert response.status_code == 403
    assert "Требуются права инженера" in response.json()["detail"]
