FROM python:3.11-slim

ARG INSTALL_DEMUCS=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ ./requirements/
RUN pip install -r requirements/base.txt \
    && if [ "$INSTALL_DEMUCS" = "true" ]; then pip install -r requirements/separation.txt; fi

COPY app/ ./app/
COPY web/ ./web/
COPY pyproject.toml README.md ./

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
