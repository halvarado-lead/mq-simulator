#!/usr/bin/env sh
set -e

export DJANGO_SETTINGS_MODULE=webapp.settings

if [ "${DB_ENGINE}" = "mysql" ]; then
	echo "Waiting for MySQL at ${DB_HOST:-mysql}:${DB_PORT:-3306}..."
	for i in 1 2 3 4 5 6 7 8 9 10; do
		nc -z ${DB_HOST:-mysql} ${DB_PORT:-3306} && break
		sleep 2
	done
fi

echo "Applying migrations (safe to run repeatedly)..."
python webapp/manage.py makemigrations mqform --noinput || true
python webapp/manage.py migrate --noinput || true

echo "Starting Django dev server on 0.0.0.0:8000"
exec python webapp/manage.py runserver 0.0.0.0:8000
