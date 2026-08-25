#!/bin/bash
# Скрипт для запуска тестов перед коммитом

echo "🧪 Запуск тестов..."
echo "====================================="

# Активируем виртуальное окружение
source .venv/Scripts/activate

# Запускаем тесты с покрытием
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Проверяем результат
if [ $? -eq 0 ]; then
    echo "✅ Все тесты пройдены успешно!"
    echo "📊 Отчёт о покрытии: ./htmlcov/index.html"
else
    echo "❌ Тесты не пройдены! Исправьте ошибки перед коммитом."
    exit 1
fi
