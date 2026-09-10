FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements-server.txt ./
RUN pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt -r requirements-server.txt

COPY *.py ./
COPY dummy_jobs.json survey_definition.json survey_definition_v3.json survey_definition_v4.json privacy_settings.json ./
COPY web-dist/ ./web-dist/
RUN groupadd --gid 10001 diana && useradd --uid 10001 --gid diana --no-create-home diana
USER diana
EXPOSE 5050
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
