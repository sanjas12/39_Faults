def test_create_article(client, auth_headers):
    """Тест создания статьи в базе знаний"""
    response = client.post(
        "/api/knowledge/",
        json={
            "title": "Тестовая статья",
            "content": "# Заголовок\n\nСодержание статьи",
            "category": "Инструкция",
            "tags": "test, knowledge",
            "is_published": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая статья"
    assert data["category"] == "Инструкция"
    assert data["is_published"] is True


def test_list_articles(client, auth_headers):
    """Тест получения списка статей"""
    response = client.get("/api/knowledge/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_article(client, auth_headers):
    """Тест получения статьи по ID"""
    # Сначала создаём статью
    create_response = client.post(
        "/api/knowledge/",
        json={
            "title": "Статья для просмотра",
            "content": "Содержание статьи",
            "category": "Документация",
            "tags": "test",
            "is_published": True,
        },
        headers=auth_headers,
    )
    article_id = create_response.json()["id"]

    response = client.get(f"/api/knowledge/{article_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == article_id
    assert data["title"] == "Статья для просмотра"


def test_get_categories(client, auth_headers):
    """Тест получения списка категорий"""
    response = client.get("/api/knowledge/categories/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_tags(client, auth_headers):
    """Тест получения списка тегов"""
    response = client.get("/api/knowledge/tags/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
