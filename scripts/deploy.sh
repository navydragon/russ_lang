#!/usr/bin/env bash
# Обновление russ_lang на продакшене после git pull / push.
# Запуск на сервере: ./scripts/deploy.sh
# Или: bash scripts/deploy.sh
#
# Имя systemd unit берётся в порядке приоритета:
#   1. переменная окружения SERVICE_NAME
#   2. GUNICORN_SERVICE из .env
#   3. автофолбэк: russ_lang, затем gunicorn_russ_lang

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${VENV_DIR:-${PROJECT_DIR}/venv}"
SERVICE_NAME_EXPLICIT="${SERVICE_NAME:-}"
SERVICE_NAME="${SERVICE_NAME:-russ_lang}"
GIT_BRANCH="${GIT_BRANCH:-main}"

log() {
    printf '\n==> %s\n' "$*"
}

die() {
    printf 'Ошибка: %s\n' "$*" >&2
    exit 1
}

# Читает значение ключа из .env проекта (первая строка с KEY=).
read_env_value() {
    local key="$1"
    local env_file="${PROJECT_DIR}/.env"
    if [[ ! -f "${env_file}" ]]; then
        return 1
    fi
    local line
    line="$(grep -E "^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=" "${env_file}" 2>/dev/null | head -1)" || true
    if [[ -z "${line}" ]]; then
        return 1
    fi
    local val="${line#*=}"
    val="${val#"${val%%[![:space:]]*}"}"
    val="${val%"${val##*[![:space:]]}"}"
    val="${val#\"}"
    val="${val%\"}"
    val="${val#\'}"
    val="${val%\'}"
    val="${val//$'\r'/}"
    printf '%s' "${val}"
}

cd "${PROJECT_DIR}"

[[ -d "${VENV_DIR}" ]] || die "venv не найден: ${VENV_DIR}"
[[ -f "${PROJECT_DIR}/manage.py" ]] || die "manage.py не найден в ${PROJECT_DIR}"

# --- Разрешение имени systemd unit ---
if [[ -n "${SERVICE_NAME_EXPLICIT}" ]]; then
    # Явно задано через окружение — используем как есть.
    SERVICE_NAME="${SERVICE_NAME_EXPLICIT%.service}"
else
    ENV_SERVICE="$(read_env_value GUNICORN_SERVICE || true)"
    ENV_SERVICE="${ENV_SERVICE%.service}"
    if [[ -n "${ENV_SERVICE}" ]]; then
        SERVICE_NAME="${ENV_SERVICE}"
    else
        # Дефолт: на сервере юниты называются gunicorn_russ_lang, gunicorn_edtech и т.п.
        SERVICE_NAME="russ_lang"
    fi
fi

if command -v systemctl >/dev/null 2>&1; then
    unit_exists() {
        systemctl cat "$1.service" >/dev/null 2>&1
    }

    # Проверяем юнит ДО git pull / migrate: лучше упасть сразу, чем в самом конце.
    if ! unit_exists "${SERVICE_NAME}"; then
        if [[ -z "${SERVICE_NAME_EXPLICIT}" ]] && unit_exists "gunicorn_${SERVICE_NAME}"; then
            log "Unit ${SERVICE_NAME}.service не найден — использую gunicorn_${SERVICE_NAME}.service"
            SERVICE_NAME="gunicorn_${SERVICE_NAME}"
        else
            die "systemd unit ${SERVICE_NAME}.service не найден. Задайте GUNICORN_SERVICE в .env (например, gunicorn_russ_lang)"
        fi
    fi
fi

log "Проект: ${PROJECT_DIR}"
log "Ветка: ${GIT_BRANCH}"

DB_FILE="${PROJECT_DIR}/db.sqlite3"
DB_PRESERVE=""

if [[ -f "${DB_FILE}" ]] && ! git check-ignore -q "${DB_FILE}" 2>/dev/null; then
    if git status --porcelain -- "${DB_FILE}" | grep -q .; then
        log "Сохраняем локальную db.sqlite3 перед git pull"
        DB_PRESERVE="$(mktemp)"
        cp "${DB_FILE}" "${DB_PRESERVE}"
        rm -f "${DB_FILE}"
    fi
fi

log "git pull origin ${GIT_BRANCH}"
git pull origin "${GIT_BRANCH}"

if [[ -n "${DB_PRESERVE}" && -f "${DB_PRESERVE}" ]]; then
    log "Восстанавливаем локальную db.sqlite3"
    cp "${DB_PRESERVE}" "${DB_FILE}"
    rm -f "${DB_PRESERVE}"
fi

log "Активация venv и установка зависимостей"
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

log "Миграции"
python manage.py migrate --noinput

log "Сбор статики"
python manage.py collectstatic --noinput

log "Проверка Django"
python manage.py check --deploy 2>/dev/null || python manage.py check

log "Перезапуск ${SERVICE_NAME}"
if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl restart "${SERVICE_NAME}"
    sudo systemctl is-active --quiet "${SERVICE_NAME}" || die "сервис ${SERVICE_NAME} не запущен"
    sudo systemctl status "${SERVICE_NAME}" --no-pager -l | head -15
else
    die "systemctl не найден — перезапустите gunicorn вручную"
fi

log "Готово"
