import pytest


def test_create_fault(client, auth_headers, test_project):
    """Тест создания неисправности"""
    response = client.post(
        "/api/faults/",
        json={
            "title": "Новая тестовая неисправность",
            "description": "Описание новой неисправности",
            "severity": "major",
            "project_id": test_project.id
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Новая тестовая неисправность"
    assert data["severity"] == "major"
    assert data["status"] == "open"


def test_list_faults(client, auth_headers, test_fault):
    """Тест получения списка неисправностей"""
    response = client.get(
        "/api/faults/",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Тестовая неисправность"


def test_get_fault(client, auth_headers, test_fault):
    """Тест получения неисправности по ID"""
    response = client.get(
        f"/api/faults/{test_fault.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_fault.id
    assert data["title"] == "Тестовая неисправность"


def test_update_fault_status(client, auth_headers, test_fault):
    """Тест обновления статуса неисправности"""
    response = client.patch(
        f"/api/faults/{test_fault.id}",
        json={"status": "in_progress"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"


def test_update_fault_severity(client, auth_headers, test_fault):
    """Тест обновления важности неисправности"""
    response = client.patch(
        f"/api/faults/{test_fault.id}",
        json={"severity": "critical"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "critical"


def test_filter_faults_by_status(client, auth_headers, test_fault):
    """Тест фильтрации неисправностей по статусу"""
    response = client.get(
        f"/api/faults/?status=open",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert all(f["status"] == "open" for f in data)


def test_delete_fault(client, auth_headers, test_fault):
    """Тест удаления неисправности"""
    response = client.delete(
        f"/api/faults/{test_fault.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    get_response = client.get(
        f"/api/faults/{test_fault.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404