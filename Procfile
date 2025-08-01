web: cd backend && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT
release: cd backend && python manage.py migrate