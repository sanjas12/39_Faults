import pytest


def test_get_fault_history(client, auth_headers, test_fault):
    """Тест получения истории неисправности"""
    # Меняем статус, чтобы создать историю
    client.patch(
        f"/api/faults/{test_fault.id}",
        json={"status": "in_progress"},
        headers=auth_headers
    )
    
    response = client.get(
        f"/api/faults/{test_fault.id}/history",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_project_history_on_update(client, auth_headers, test_project):
    """Тест записи истории при обновлении проекта"""
    client.put(
        f"/api/projects/{test_project.id}",
        json={"name": "Обновлённое название"},
        headers=auth_headers
    )
    
    response = client.get(
        f"/api/projects/{test_project.id}/history",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["field"] == "Название"