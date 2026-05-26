#!/bin/bash

# uv + интернет → uv sync (если есть pyproject.toml) или uv pip install -r requirements.txt
# uv + офлайн → uv sync --no-index --find-links=... или uv pip install --no-index
# нет uv + интернет → fallback на pip install -r requirements.txt
# нет uv + офлайн → fallback на pip install --no-index -f ...
set -e

cd "$(dirname "$0")/.." || exit 1

# ── НАСТРОЙКА ЛОГИРОВАНИЯ ───────────────────────────────────────────────────
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/venv_pip_$(date +%Y%m%d_%H%M%S).log"
ERROR_LOG="$LOG_DIR/venv_pip_errors.log"

# Функция логирования
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$timestamp - $1" | tee -a "$LOG_FILE"
}

# Функция логирования ошибок
log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$timestamp - ❌ $1" | tee -a "$LOG_FILE" "$ERROR_LOG"
}

# Функция логирования успеха
log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$timestamp - ✅ $1" | tee -a "$LOG_FILE"
}

# Функция логирования предупреждений
log_warning() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$timestamp - ⚠ $1" | tee -a "$LOG_FILE"
}

# Обработчик ошибок
error_handler() {
    local line_no=$1
    local command=$2
    local exit_code=$3
    
    log_error "Ошибка на строке $line_no"
    log_error "Команда: $command"
    log_error "Код возврата: $exit_code"
    log_error "Текущая директория: $(pwd)"
    log_error "Скрипт завершен с ошибкой. Лог: $LOG_FILE"
    
    exit $exit_code
}

trap 'error_handler ${LINENO} "$BASH_COMMAND" $?' ERR

# ── Вспомогательные функции ───────────────────────────────────────────────────
activate_venv() {
    if [[ -f ".venv/Scripts/activate" ]]; then
        source .venv/Scripts/activate
        log_success "venv активирована (Windows)"
    elif [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        log_success "venv активирована (Linux/Mac)"
    else
        log_error "activate не найден"
        exit 1
    fi
}

# --- CONFIG ---
PIP_VERSION="25.0.1"

log "=== НАЧАЛО BOOTSTRAP ==="
log "Лог-файл: $LOG_FILE"

# Поиск LOCAL_PACKAGES_DIR на дисках D, E, F
LOCAL_PACKAGES_DIR=""
for drive in d e f; do
    candidate="/$drive/temp/python_Library"
    if [[ -d "$candidate" ]]; then
        LOCAL_PACKAGES_DIR="$candidate"
        log_success "локальный каталог найден: $LOCAL_PACKAGES_DIR"
        break
    fi
done

if [[ -z "$LOCAL_PACKAGES_DIR" ]]; then
    log_warning "локальный каталог python_Library не найден ни на одном из дисков (d/e/f)"
fi

# --- CLEAN ---
log "удаляем .venv ..."
rm -rf .venv
log_success ".venv удален"

# --- DETECT UV ---
if command -v uv >/dev/null 2>&1; then
    HAS_UV=1
    log_success "uv найден"
else
    HAS_UV=0
    log_warning "uv не найден -> fallback на pip"
fi

# интернет
log "Проверка доступа в интернет..."
set +e
python - <<EOF 2>/dev/null
import urllib.request
urllib.request.urlopen("https://pypi.org/simple/", timeout=3)
EOF
NET_OK=$?
set -e

if [ $NET_OK -eq 0 ]; then
    log_success "Интернет доступен"
else
    log_warning "Интернет НЕ доступен"
fi

# --- DETECT PROJECT TYPE ---
[ -f "pyproject.toml" ] && USE_PYPROJECT=1 || USE_PYPROJECT=0

if [ $USE_PYPROJECT -eq 1 ]; then
    log "Тип проекта: pyproject.toml"
else
    log "Тип проекта: requirements.txt"
fi

if [ $USE_PYPROJECT -eq 0 ] && [ ! -f "requirements.txt" ]; then
    log_error "нет зависимостей"
    exit 1
fi

if [ $NET_OK -ne 0 ] && [ ! -d "$LOCAL_PACKAGES_DIR" ]; then
    log_error "нет офлайн-каталога: $LOCAL_PACKAGES_DIR"
    exit 1
fi

# --- MODE FLAGS ---
USE_OFFLINE=0
[ $NET_OK -ne 0 ] && USE_OFFLINE=1

PIP_ARGS=()
[ $USE_OFFLINE -eq 1 ] && PIP_ARGS+=(--no-index --find-links="$LOCAL_PACKAGES_DIR")

if [ $USE_OFFLINE -eq 1 ]; then
    log "Режим: ОФЛАЙН"
else
    log "Режим: ОНЛАЙН"
fi

# ─────────────────────────────────────────────────────────────────────────────
# INSTALL WITH UV
# ─────────────────────────────────────────────────────────────────────────────
install_with_uv() {
    log "=== УСТАНОВКА ЧЕРЕЗ UV ==="
    
    log "Создание виртуального окружения..."
    uv venv
    log_success "Виртуальное окружение создано"

    if [ $USE_PYPROJECT -eq 1 ]; then
        UV_ARGS=(--group build)
        [ $USE_OFFLINE -eq 1 ] && UV_ARGS+=(--no-index --find-links="$LOCAL_PACKAGES_DIR" --frozen)

        log "Выполнение: uv sync ${UV_ARGS[*]}"
        uv sync "${UV_ARGS[@]}"
        log_success "Зависимости установлены через uv sync"
    else
        log "Выполнение: uv pip install с параметрами ${PIP_ARGS[*]}"
        # dry-run
        uv pip install "${PIP_ARGS[@]}" -r requirements.txt --dry-run
        log "Dry-run выполнен успешно"
        # install
        uv pip install "${PIP_ARGS[@]}" -r requirements.txt
        log_success "Зависимости установлены через uv pip"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# INSTALL WITH PIP
# ─────────────────────────────────────────────────────────────────────────────
install_with_pip() {
    log "=== УСТАНОВКА ЧЕРЕЗ PIP ==="

    log "Создание виртуального окружения..."
    python -m venv .venv
    log_success "Виртуальное окружение создано"
    
    activate_venv

    # обновление pip
    log "Обновление pip до версии $PIP_VERSION..."
    python -m pip install "${PIP_ARGS[@]}" --upgrade pip=="$PIP_VERSION"
    log_success "Pip обновлен"

    # dry-run (если доступен)
    if python -m pip install --help | grep -q -- "--dry-run"; then
        log "Выполнение dry-run..."
        pip install "${PIP_ARGS[@]}" -r requirements.txt --dry-run
        log_success "Dry-run выполнен"
    else
        log_warning "pip без --dry-run, пропускаем проверку"
    fi

    log "Установка зависимостей..."
    pip install "${PIP_ARGS[@]}" -r requirements.txt
    log_success "Зависимости установлены через pip"
}

# ─────────────────────────────────────────────────────────────────────────────
# INSTALL GIT HOOKS
# ─────────────────────────────────────────────────────────────────────────────
install_hooks() {
    log "=== УСТАНОВКА GIT HOOKS ==="

    if [ ! -d ".git" ]; then
        log_error "это не git репозиторий"
        exit 1
    fi

    if command -v uv >/dev/null 2>&1; then
        log "Установка pre-commit hooks через uv..."
        uv run pre-commit install
        uv run pre-commit install --hook-type commit-msg
        log_success "Git hooks установлены через uv"
    else
        log "Установка pre-commit hooks..."
        pre-commit install
        pre-commit install --hook-type commit-msg
        log_success "Git hooks установлены через pre-commit"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────
START_TIME=$(date +%s)

log "=== START BOOTSTRAP ==="

if [ $HAS_UV -eq 1 ]; then
    install_with_uv
else
    install_with_pip
fi

install_hooks

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log_success "=== ГОТОВО ==="
log_success "Окружение + зависимости + git hooks готовы"
log_success "Время выполнения: ${DURATION} секунд"
log_success "Полный лог: $LOG_FILE"

echo ""
echo "🎉 ГОТОВО: окружение + зависимости + git hooks готовы"
echo "📝 Лог сохранен в: $LOG_FILE"