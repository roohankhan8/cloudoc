FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && adduser --system --group --uid 10001 app

COPY --chown=app:app config ./config
COPY --chown=app:app documents ./documents
COPY --chown=app:app templates ./templates
COPY --chown=app:app manage.py .

USER app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
