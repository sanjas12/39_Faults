# Инструкции для агентов

## Проверки Python-кода

- После изменения Python-файлов обязательно запускай `mypy` для всех затронутых
  исходных файлов до завершения задачи. Исправляй все новые ошибки типизации.
- Дополнительно запускай синтаксическую проверку и релевантные тесты. Если штатное
  окружение проекта не работает, используй доступный интерпретатор для тех проверок,
  которые можно выполнить, и явно сообщи, какие проверки запустить не удалось.
- Не считай успешную компиляцию заменой `mypy`: синтаксическая проверка не выявляет
  ошибки обращения к значениям типа `Optional`.

## Работа с Optional

- Не вызывай методы непосредственно у атрибута типа `Optional`, даже сразу после
  присваивания: `mypy` может не сохранять сужение типа изменяемого атрибута объекта.
- Сначала сохрани гарантированно созданный объект в локальную переменную, работай с
  ней, а затем присвой её атрибуту. При чтении существующего optional-атрибута также
  скопируй его в локальную переменную и явно проверь на `None` перед использованием.

Пример:

```python
annotation = axis.annotate(...)
annotation.set_visible(False)
self._annotation = annotation

current_annotation = self._annotation
if current_annotation is None:
    return
current_annotation.set_visible(True)
```

## Пользовательская документация

- После каждого крупного изменения функциональности обновляй
  `docs/USER_MANUAL.md`: назначение функции, действия пользователя, настройки,
  формат результатов и важные ограничения.
- Если изменение затрагивает установку, запуск, сборку, выпуск версии или основные
  возможности проекта, при необходимости обновляй также корневой `Readme.md`.
- Поддерживай номер версии и дату обновления руководства в актуальном состоянии.


## Local server policy

- Never start a local application or development server in this repository.
- Do not run Uvicorn, `scripts/run_uv.sh`, `scripts/run_pip.sh`, or any command that opens or listens on a local network port.
- Do not launch the application in a browser or perform browser-based UI testing against localhost.
- The user performs all application startup and visual UI verification manually.
- Validate changes only with non-server checks such as template compilation, static analysis, linters, and automated tests that do not start a listening server.
- If completing a request appears to require a local server, stop and ask the user to perform that verification instead.
