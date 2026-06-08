#!/usr/bin/env bash
# Обновление russ_lang на продакшене после git pull / push.
# Запуск на сервере: ./scripts/deploy.sh
# Или: bash scripts/deploy.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${VENV_DIR:-${PROJECT_DIR}/venv}"
SERVICE_NAME="${SERVICE_NAME:-russ_lang}"
GIT_BRANCH="${GIT_BRANCH:-main}"

log() {
    printf '\n==> %s\n' "$*"
}

die() {
    printf 'Ошибка: %s\n' "$*" >&2
    exit 1
}

cd "${PROJECT_DIR}"

[[ -d "${VENV_DIR}" ]] || die "venv не найден: ${VENV_DIR}"
[[ -f "${PROJECT_DIR}/manage.py" ]] || die "manage.py не найден в ${PROJECT_DIR}"

log "Проект: ${PROJECT_DIR}"
log "Ветка: ${GIT_BRANCH}"

log "git pull origin ${GIT_BRANCH}"
git pull origin "${GIT_BRANCH}"

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
