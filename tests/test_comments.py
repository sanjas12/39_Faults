def test_add_comment(client, auth_headers, test_fault):
    """Тест добавления комментария"""
    response = client.post(
        f"/api/faults/{test_fault.id}/comments",
        json={
            "content": "Тестовый комментарий",
            "is_internal": False,
            "author": "testuser",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Тестовый комментарий"
    assert data["author"] == "testuser"


def test_list_comments(client, auth_headers, test_fault):
    """Тест получения списка комментариев"""
    # Сначала добавляем комментарий
    client.post(
        f"/api/faults/{test_fault.id}/comments",
        json={
            "content": "Комментарий для списка",
            "is_internal": False,
            "author": "testuser",
        },
        headers=auth_headers,
    )

    response = client.get(f"/api/faults/{test_fault.id}/comments", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["content"] == "Комментарий для списка"


def test_add_internal_comment(client, auth_headers, test_fault):
    """Тест добавления внутреннего комментария"""
    response = client.post(
        f"/api/faults/{test_fault.id}/comments",
        json={
            "content": "Внутренний комментарий",
            "is_internal": True,
            "author": "testuser",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["is_internal"] is True
