def test_get_fault_history(client, auth_headers, test_fault):
    """Тест получения истории неисправности"""
    # Меняем статус, чтобы создать историю
    response = client.patch(
        f"/api/faults/{test_fault.id}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Проверяем историю
    history_response = client.get(
        f"/api/faults/{test_fault.id}/history", headers=auth_headers
    )

    assert history_response.status_code == 200
    data = history_response.json()
    assert len(data) >= 1


def test_project_history_on_update(client, engineer_headers, test_project):
    """Тест записи истории при обновлении проекта (требуются права ENGINEER)"""
    # Обновляем проект
    response = client.put(
        f"/api/projects/{test_project.id}",
        json={"name": "Обновлённое название"},
        headers=engineer_headers,  # ✅ Используем инженера
    )

    assert response.status_code == 200

    # Проверяем историю
    history_response = client.get(
        f"/api/projects/{test_project.id}/history", headers=engineer_headers
    )

    assert history_response.status_code == 200
    data = history_response.json()

    # Проверяем, что история записалась
    assert len(data) >= 1
    # Проверяем, что это запись об изменении названия
    assert data[0]["field"] == "Название" or data[0]["field"] == "name"
    assert data[0]["old_value"] == "Тестовый проект"
    assert data[0]["new_value"] == "Обновлённое название"


def test_project_history_on_creation(client, engineer_headers):
    """Тест записи истории при создании проекта"""
    # Создаём проект
    response = client.post(
        "/api/projects/",
        json={
            "name": "Проект для истории",
            "description": "Описание",
            "client": "Клиент",
        },
        headers=engineer_headers,
    )

    assert response.status_code == 201
    project_id = response.json()["id"]

    # Проверяем историю
    history_response = client.get(
        f"/api/projects/{project_id}/history", headers=engineer_headers
    )

    assert history_response.status_code == 200
    data = history_response.json()

    # Должна быть запись о создании
    assert len(data) >= 1
    assert data[0]["event_type"] == "creation"
