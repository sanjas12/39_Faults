#!/bin/bash

# uv + интернет → uv sync (если есть pyproject.toml) или uv pip install -r requirements.txt
# uv + офлайн → uv sync --no-index --find-links=... или uv pip install --no-index
# нет uv + интернет → fallback на pip install -r requirements.txt
# нет uv + офлайн → fallback на pip install --no-index -f ...
set -e

cd "$(dirname "$0")/.." || exit 1

# ── Вспомогательные функции ───────────────────────────────────────────────────
log() {
    echo -e "$1"
}

activate_venv() {
    if [[ -f ".venv/Scripts/activate" ]]; then
        source .venv/Scripts/activate
        echo "venv активирована (Windows)"
    elif [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        echo "venv активирована (Linux/Mac)"
    else
        echo "❌ activate не найден"
        exit 1
    fi
}

# --- CONFIG ---
PIP_VERSION="25.0.1"

# Поиск LOCAL_PACKAGES_DIR на дисках D, E, F
LOCAL_PACKAGES_DIR=""
for drive in d e f; do
    candidate="/$drive/temp/python_Library"
    if [[ -d "$candidate" ]]; then
        LOCAL_PACKAGES_DIR="$candidate"
        log "📦 локальный каталог найден: $LOCAL_PACKAGES_DIR"
        break
    fi
done

if [[ -z "$LOCAL_PACKAGES_DIR" ]]; then
    log "⚠ локальный каталог python_Library не найден ни на одном из дисков (d/e/f)"
fi

# --- CLEAN ---
log "удаляем .venv ..."
rm -rf .venv

# --- DETECT UV ---
if command -v uv >/dev/null 2>&1; then
    HAS_UV=1
    log "uv найден"
else
    HAS_UV=0
    log "uv  не найден -> fallback на pip"
fi

# интернет
set +e
python - <<EOF 2>/dev/null
import urllib.request
urllib.request.urlopen("https://pypi.org/simple/", timeout=3)
EOF
NET_OK=$?
set -e

# --- DETECT PROJECT TYPE ---
[ -f "pyproject.toml" ] && USE_PYPROJECT=1 || USE_PYPROJECT=0

if [ $USE_PYPROJECT -eq 0 ] && [ ! -f "requirements.txt" ]; then
    echo "❌ нет зависимостей"
    exit 1
fi

if [ $NET_OK -ne 0 ] && [ ! -d "$LOCAL_PACKAGES_DIR" ]; then
    echo "❌ нет офлайн-каталога: $LOCAL_PACKAGES_DIR"
    exit 1
fi

# --- MODE FLAGS ---
USE_OFFLINE=0
[ $NET_OK -ne 0 ] && USE_OFFLINE=1

PIP_ARGS=()
[ $USE_OFFLINE -eq 1 ] && PIP_ARGS+=(--no-index --find-links="$LOCAL_PACKAGES_DIR")

# ─────────────────────────────────────────────────────────────────────────────
# INSTALL WITH UV
# ─────────────────────────────────────────────────────────────────────────────
install_with_uv() {
    log "⚡ uv режим"

    uv venv

    if [ $USE_PYPROJECT -eq 1 ]; then
        UV_ARGS=(--group build)
        [ $USE_OFFLINE -eq 1 ] && UV_ARGS+=(--no-index --find-links="$LOCAL_PACKAGES_DIR" --frozen)

        uv sync "${UV_ARGS[@]}"
    else
        # dry-run
        uv pip install "${PIP_ARGS[@]}" -r requirements.txt --dry-run
        # install
        uv pip install "${PIP_ARGS[@]}" -r requirements.txt
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# INSTALL WITH PIP
# ─────────────────────────────────────────────────────────────────────────────
install_with_pip() {
    log "установка через pip"

    python -m venv .venv
    activate_venv

    # обновление pip
    python -m pip install "${PIP_ARGS[@]}" --upgrade pip=="$PIP_VERSION"


    # dry-run (если доступен)
    if python -m pip install --help | grep -q -- "--dry-run"; then
        pip install "${PIP_ARGS[@]}" -r requirements.txt --dry-run
    else
        log "⚠ pip без --dry-run, пропускаем проверку"
    fi

    pip install "${PIP_ARGS[@]}" -r requirements.txt
}

# ─────────────────────────────────────────────────────────────────────────────
# INSTALL GIT HOOKS
# ─────────────────────────────────────────────────────────────────────────────
install_hooks() {
    log "🔗 установка git hooks"

    if [ ! -d ".git" ]; then
        echo "❌ это не git репозиторий"
        exit 1
    fi

    if command -v uv >/dev/null 2>&1; then
        uv run pre-commit install
        uv run pre-commit install --hook-type commit-msg
    else
        pre-commit install
        pre-commit install --hook-type commit-msg
    fi

    log "✅ git hooks установлены"
}

# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────
log "=== START BOOTSTRAP ==="

if [ $HAS_UV -eq 1 ]; then
    install_with_uv
else
    install_with_pip
fi

install_hooks

log "🎉 ГОТОВО: окружение + зависимости + git hooks готовы"
