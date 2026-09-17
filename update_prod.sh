#!/usr/bin/env bash
# Обновление продакшена russ_lang одной командой:
#   ./update_prod.sh
#   ./update_prod.sh main
#
# Шаги: git pull → pip install → migrate → collectstatic → restart gunicorn (systemd).
#
# Переменные в .env (опционально):
#   GUNICORN_SERVICE=russ_lang   — имя systemd unit (по умолчанию)
#
# Альтернатива: scripts/deploy.sh (тот же сервис russ_lang).

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
  cat <<'EOF'
Использование: ./update_prod.sh [ветка|ref]

Примеры:
  ./update_prod.sh           # git pull текущей ветки
  ./update_prod.sh main      # git fetch + checkout main + pull

Запуск: только на Linux-сервере (не в Git Bash на Windows).
  ssh <host>
  cd ~/russ_lang   # или путь к клону проекта
  ./update_prod.sh

Переменные в .env:
  GUNICORN_SERVICE=russ_lang
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# Скрипт только для Linux-сервера с systemd (не Windows / Git Bash).
case "$(uname -s 2>/dev/null || echo unknown)" in
  MINGW*|MSYS*|CYGWIN*|Windows*)
    log_error "update_prod.sh предназначен для Linux-сервера с gunicorn + systemd."
    log_error "На Windows запускать не нужно. Подключитесь по SSH:"
    log_error "  ssh <host>"
    log_error "  cd ~/russ_lang && ./update_prod.sh"
    exit 1
    ;;
esac

if ! command -v systemctl &>/dev/null; then
  log_error "systemctl не найден. Скрипт рассчитан на продакшен с systemd."
  exit 1
fi

if ! command -v sudo &>/dev/null; then
  log_error "sudo не найден. На сервере установите sudo или запустите systemctl от root."
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

ENV_FILE="${PROJECT_DIR}/.env"
GIT_REF="${1:-}"

read_env_value() {
  local key="$1"
  if [[ ! -f "$ENV_FILE" ]]; then
    return 1
  fi
  local line
  line="$(grep -E "^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=" "$ENV_FILE" 2>/dev/null | head -1)" || true
  if [[ -z "$line" ]]; then
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
  printf '%s' "$val"
}

if [[ ! -d "${PROJECT_DIR}/venv" ]]; then
  log_error "Каталог venv не найден: ${PROJECT_DIR}/venv"
  exit 1
fi

if [[ ! -f "${PROJECT_DIR}/requirements.txt" ]]; then
  log_error "Файл requirements.txt не найден"
  exit 1
fi

if [[ ! -f "${PROJECT_DIR}/manage.py" ]]; then
  log_error "manage.py не найден — скрипт должен лежать в корне russ_lang"
  exit 1
fi

GUNICORN_SERVICE="$(read_env_value GUNICORN_SERVICE || true)"
GUNICORN_SERVICE="${GUNICORN_SERVICE:-russ_lang}"
# systemctl принимает и russ_lang, и russ_lang.service
GUNICORN_SERVICE="${GUNICORN_SERVICE%.service}"

log_info "Директория проекта: ${PROJECT_DIR}"
log_info "Systemd unit: ${GUNICORN_SERVICE}"

if ! command -v git &>/dev/null; then
  log_error "git не найден"
  exit 1
fi

if [[ -n "$GIT_REF" ]]; then
  log_info "Обновление кода: fetch + checkout ${GIT_REF}..."
  git fetch --all --prune
  git checkout "$GIT_REF"
  git pull --ff-only origin "$GIT_REF"
else
  log_info "Обновление кода: git pull..."
  git pull --ff-only
fi

log_info "Активация venv..."
# shellcheck source=/dev/null
source "${PROJECT_DIR}/venv/bin/activate"

log_info "Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

log_info "Миграции Django..."
python manage.py migrate --noinput

log_info "Сбор статических файлов..."
python manage.py collectstatic --noinput

log_info "Перезапуск gunicorn: sudo systemctl restart ${GUNICORN_SERVICE}"
sudo systemctl restart "${GUNICORN_SERVICE}"

sleep 2
if sudo systemctl is-active --quiet "${GUNICORN_SERVICE}"; then
  log_info "Сервис ${GUNICORN_SERVICE} запущен"
else
  log_error "Сервис не активен. Логи: sudo journalctl -u ${GUNICORN_SERVICE} -n 50 --no-pager"
  exit 1
fi

log_info "Обновление завершено."
log_info "Статус: sudo systemctl status ${GUNICORN_SERVICE}"
log_info "Логи:   sudo journalctl -u ${GUNICORN_SERVICE} -f"
