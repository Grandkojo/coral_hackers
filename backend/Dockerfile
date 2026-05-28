FROM python:3.12-slim-bookworm

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates bash \
  && rm -rf /var/lib/apt/lists/*

# Coral CLI (Linux install script → ~/.local/bin/coral)
RUN curl -fsSL https://withcoral.com/install.sh | sh

ENV PATH="/root/.local/bin:${PATH}" \
    CORAL_BINARY=coral \
    CORAL_CONFIG_DIR=/data/coral \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

RUN sed -i 's/\r$//' /app/scripts/*.sh \
  && chmod +x /app/scripts/docker-entrypoint.sh /app/scripts/setup_coral_sources.sh

EXPOSE 8000

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
